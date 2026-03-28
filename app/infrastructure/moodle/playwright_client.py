from __future__ import annotations

import re
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import AsyncIterator
from urllib.parse import parse_qs, urlparse

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from app.domain.exceptions import MoodleAuthenticationError, MoodleScrapingError
from app.domain.models.task import Task
from app.domain.ports.moodle_client import MoodleClient
from app.infrastructure.moodle.parser import MoodleTaskParser, RawTaskData
from app.infrastructure.moodle.selectors import (
    LOGIN_SELECTORS,
    NAVIGATION_SELECTORS,
    TASK_SELECTORS,
)


@dataclass(frozen=True, slots=True)
class TimelineEvent:
    """
    Lightweight representation of a Moodle timeline item before conversion into
    a domain task.
    """

    task_id: str
    title: str
    course_name: str
    url: str
    due_at: datetime | None
    submission_status_raw: str | None


class PlaywrightMoodleClient(MoodleClient):
    """
    Playwright-backed Moodle client.

    This adapter logs into Moodle, reads the dashboard timeline to obtain the
    current pending task snapshot, and can open a specific activity page to
    scrape richer task detail for AI assistance.

    Design notes:
    - each public operation uses a fresh browser context
    - login is handled internally on each operation
    - dashboard scraping is optimized around the timeline block
    - assign detail pages are parsed with richer selectors confirmed from the
      provided Moodle HTML
    """

    def __init__(
        self,
        *,
        base_url: str,
        username: str,
        password: str,
        parser: MoodleTaskParser,
        headless: bool = True,
        slow_mo_ms: int = 0,
        navigation_timeout_ms: int = 30_000,
    ) -> None:
        normalized_base_url = base_url.strip().rstrip("/")
        normalized_username = username.strip()

        if not normalized_base_url:
            msg = "Moodle base URL must not be empty."
            raise ValueError(msg)

        if not normalized_username:
            msg = "Moodle username must not be empty."
            raise ValueError(msg)

        if not password.strip():
            msg = "Moodle password must not be empty."
            raise ValueError(msg)

        if navigation_timeout_ms <= 0:
            msg = "navigation_timeout_ms must be greater than zero."
            raise ValueError(msg)

        self._base_url = normalized_base_url
        self._username = normalized_username
        self._password = password
        self._parser = parser
        self._headless = headless
        self._slow_mo_ms = slow_mo_ms
        self._navigation_timeout_ms = navigation_timeout_ms

    async def fetch_tasks(self) -> list[Task]:
        """
        Fetch the current task snapshot from the Moodle dashboard timeline.
        """
        async with self._authenticated_page() as page:
            await page.goto(
                f"{self._base_url}/my/",
                wait_until="domcontentloaded",
            )
            await self._wait_for_dashboard(page)

            timeline_events = await self._extract_timeline_events(page)
            raw_tasks = [
                self._parser.build_raw_task(
                    id=event.task_id,
                    title=event.title,
                    course_name=event.course_name,
                    url=event.url,
                    due_at=event.due_at,
                    submission_status_raw=event.submission_status_raw,
                    base_url=self._base_url,
                )
                for event in timeline_events
            ]
            return self._parser.parse_many(raw_tasks)

    async def fetch_task_detail(self, task_url: str) -> Task:
        """
        Fetch a single task detail page and return a normalized task.

        For assign pages, this method extracts rich detail from the confirmed
        structure of the assignment page. For other activity types, it falls
        back to a generic page extraction strategy.
        """
        normalized_task_url = task_url.strip()
        if not normalized_task_url:
            msg = "Task URL must not be empty."
            raise MoodleScrapingError(msg)

        async with self._authenticated_page() as page:
            await page.goto(
                normalized_task_url,
                wait_until="domcontentloaded",
            )
            await self._wait_for_main_content(page)

            if "/mod/assign/view.php" in page.url:
                raw_task = await self._extract_assign_task_detail(page)
            else:
                raw_task = await self._extract_generic_task_detail(page)

            return self._parser.parse_one(raw_task)

    @asynccontextmanager
    async def _authenticated_page(self) -> AsyncIterator[Page]:
        browser: Browser | None = None
        context: BrowserContext | None = None

        try:
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(
                headless=self._headless,
                slow_mo=self._slow_mo_ms,
            )
            context = await browser.new_context()
            page = await context.new_page()
            page.set_default_timeout(self._navigation_timeout_ms)

            await self._login(page)
            yield page
        except MoodleAuthenticationError:
            raise
        except MoodleScrapingError:
            raise
        except Exception as exc:
            msg = f"Unexpected Moodle browser automation error: {exc!s}"
            raise MoodleScrapingError(msg) from exc
        finally:
            if context is not None:
                await context.close()
            if browser is not None:
                await browser.close()
            try:
                await playwright.stop()
            except Exception:
                pass

    async def _login(self, page: Page) -> None:
        await page.goto(
            f"{self._base_url}/login/index.php",
            wait_until="domcontentloaded",
        )
        await self._wait_for_any(page, NAVIGATION_SELECTORS.page_ready_candidates)

        username_locator = page.locator(LOGIN_SELECTORS.username_input)
        password_locator = page.locator(LOGIN_SELECTORS.password_input)

        if await username_locator.count() == 0 or await password_locator.count() == 0:
            if "/my/" in page.url or "page-my-index" in await page.locator("body").get_attribute("id") or False:
                return

            msg = "Moodle login form could not be found."
            raise MoodleAuthenticationError(msg)

        await username_locator.first.fill(self._username)
        await password_locator.first.fill(self._password)

        submit_locator = page.locator(LOGIN_SELECTORS.submit_button).first
        await submit_locator.click()
        await page.wait_for_load_state("domcontentloaded")

        if await username_locator.count() > 0 and await password_locator.count() > 0:
            error_message = await self._extract_first_visible_text(
                page=page,
                selectors=LOGIN_SELECTORS.login_error_candidates,
            )
            detail = error_message or "Login form is still present after submission."
            msg = f"Moodle authentication failed: {detail}"
            raise MoodleAuthenticationError(msg)

        await self._wait_for_any(page, NAVIGATION_SELECTORS.page_ready_candidates)

    async def _wait_for_dashboard(self, page: Page) -> None:
        try:
            await page.wait_for_selector("#block-timeline", timeout=self._navigation_timeout_ms)
        except Exception as exc:
            msg = "Moodle dashboard timeline block could not be found."
            raise MoodleScrapingError(msg) from exc

    async def _wait_for_main_content(self, page: Page) -> None:
        await self._wait_for_any(page, NAVIGATION_SELECTORS.main_content_candidates)

    async def _wait_for_any(self, page: Page, selectors: tuple[str, ...]) -> None:
        last_error: Exception | None = None

        for selector in selectors:
            try:
                await page.wait_for_selector(selector, timeout=5_000)
                return
            except Exception as exc:
                last_error = exc

        msg = f"None of the expected page selectors were found: {selectors!r}"
        raise MoodleScrapingError(msg) from last_error

    async def _extract_timeline_events(self, page: Page) -> list[TimelineEvent]:
        timeline_items = page.locator('#block-timeline [data-region="event-list-item"]')
        item_count = await timeline_items.count()

        if item_count == 0:
            return []

        events: list[TimelineEvent] = []

        for index in range(item_count):
            item = timeline_items.nth(index)

            title = await self._safe_inner_text(item, "h6.event-name")
            course_name = await self._safe_inner_text(item, "small.text-muted")
            due_date_text = await self._resolve_timeline_date_heading(item)
            time_text = await self._safe_inner_text(item, "small.text-right")

            primary_link = item.locator('a[href*="/mod/assign/view.php"], a[href*="/mod/quiz/view.php"]').first
            href = await primary_link.get_attribute("href")

            if href is None:
                continue

            absolute_url = self._absolute_url(href)
            task_id = self._extract_activity_id(absolute_url)

            if task_id is None:
                continue

            due_at = self._parse_spanish_datetime(
                date_text=due_date_text,
                time_text=time_text,
            )

            submission_action_text = await self._extract_submission_action_text(item)
            normalized_status = self._infer_status_from_timeline_item(
                title=title,
                action_text=submission_action_text,
            )

            events.append(
                TimelineEvent(
                    task_id=task_id,
                    title=self._strip_due_suffix(title),
                    course_name=course_name,
                    url=absolute_url,
                    due_at=due_at,
                    submission_status_raw=normalized_status,
                )
            )

        return events

    async def _extract_assign_task_detail(self, page: Page) -> RawTaskData:
        task_id = self._extract_activity_id(page.url)
        if task_id is None:
            msg = f"Could not extract activity id from assign URL: {page.url}"
            raise MoodleScrapingError(msg)

        title = await self._safe_inner_text(page, "h2")
        course_name = await self._extract_first_visible_text(
            page=page,
            selectors=TASK_SELECTORS.course_name_candidates,
        )
        if course_name is None:
            course_name = await self._safe_inner_text(page, ".page-header-headings h1")

        description_html = await self._extract_optional_inner_html(page, "#intro")
        due_at = await self._extract_status_table_datetime(page, label="Fecha de entrega")
        submission_status_raw = await self._extract_status_table_value(page, label="Estado de la entrega")

        return self._parser.build_raw_task(
            id=task_id,
            title=title,
            course_name=course_name,
            url=page.url,
            description_html=description_html,
            due_at=due_at,
            submission_status_raw=submission_status_raw,
            base_url=self._base_url,
        )

    async def _extract_generic_task_detail(self, page: Page) -> RawTaskData:
        task_id = self._extract_activity_id(page.url)
        if task_id is None:
            msg = f"Could not extract activity id from activity URL: {page.url}"
            raise MoodleScrapingError(msg)

        title = await self._extract_first_visible_text(page=page, selectors=TASK_SELECTORS.title_candidates)
        if title is None:
            title = await self._safe_inner_text(page, "h2")

        course_name = await self._extract_first_visible_text(
            page=page,
            selectors=TASK_SELECTORS.course_name_candidates,
        )
        if course_name is None:
            msg = "Could not extract course name from Moodle activity page."
            raise MoodleScrapingError(msg)

        description_html = await self._extract_first_inner_html(
            page=page,
            selectors=TASK_SELECTORS.description_candidates,
        )

        due_at = await self._extract_first_datetime_from_page(page)
        submission_status_raw = await self._extract_first_visible_text(
            page=page,
            selectors=TASK_SELECTORS.submission_status_candidates,
        )

        return self._parser.build_raw_task(
            id=task_id,
            title=title,
            course_name=course_name,
            url=page.url,
            description_html=description_html,
            due_at=due_at,
            submission_status_raw=submission_status_raw,
            base_url=self._base_url,
        )

    async def _resolve_timeline_date_heading(self, item) -> str:
        heading_locator = item.locator("xpath=ancestor::div[contains(@class, 'border-bottom')][1]//h5").first
        if await heading_locator.count() > 0:
            text = await heading_locator.inner_text()
            normalized = text.strip()
            if normalized:
                return normalized

        msg = "Could not resolve timeline date heading for Moodle event item."
        raise MoodleScrapingError(msg)

    async def _extract_submission_action_text(self, item) -> str | None:
        action_link = item.locator("h6.pt-2 a").first
        if await action_link.count() == 0:
            return None

        text = await action_link.inner_text()
        normalized = text.strip()
        return normalized or None

    async def _extract_status_table_value(self, page: Page, *, label: str) -> str | None:
        rows = page.locator(".submissionstatustable table.generaltable tr")
        row_count = await rows.count()

        for index in range(row_count):
            row = rows.nth(index)
            header = row.locator("th").first
            if await header.count() == 0:
                continue

            header_text = (await header.inner_text()).strip()
            if header_text.casefold() != label.casefold():
                continue

            value_cell = row.locator("td").first
            if await value_cell.count() == 0:
                return None

            value_text = (await value_cell.inner_text()).strip()
            return value_text or None

        return None

    async def _extract_status_table_datetime(self, page: Page, *, label: str) -> datetime | None:
        value_text = await self._extract_status_table_value(page, label=label)
        if value_text is None:
            return None

        return self._parse_full_spanish_datetime(value_text)

    async def _extract_first_datetime_from_page(self, page: Page) -> datetime | None:
        main_text = await page.locator("#region-main").inner_text()
        match = re.search(
            r"([a-záéíóúñ]+,\s+\d{1,2}\s+de\s+[a-záéíóúñ]+\s+de\s+\d{4},\s+\d{1,2}:\d{2})",
            main_text,
            flags=re.IGNORECASE,
        )
        if match is None:
            return None

        return self._parse_full_spanish_datetime(match.group(1))

    async def _extract_first_visible_text(
        self,
        *,
        page: Page,
        selectors: tuple[str, ...],
    ) -> str | None:
        for selector in selectors:
            locator = page.locator(selector).first
            if await locator.count() == 0:
                continue

            text = (await locator.inner_text()).strip()
            if text:
                return text

        return None

    async def _extract_first_inner_html(
        self,
        *,
        page: Page,
        selectors: tuple[str, ...],
    ) -> str | None:
        for selector in selectors:
            locator = page.locator(selector).first
            if await locator.count() == 0:
                continue

            html = (await locator.inner_html()).strip()
            if html:
                return html

        return None

    async def _extract_optional_inner_html(self, page: Page, selector: str) -> str | None:
        locator = page.locator(selector).first
        if await locator.count() == 0:
            return None

        html = (await locator.inner_html()).strip()
        return html or None

    async def _safe_inner_text(self, page_or_locator, selector: str) -> str:
        locator = page_or_locator.locator(selector).first
        if await locator.count() == 0:
            msg = f"Required Moodle selector was not found: {selector}"
            raise MoodleScrapingError(msg)

        text = (await locator.inner_text()).strip()
        if not text:
            msg = f"Moodle selector was found but empty: {selector}"
            raise MoodleScrapingError(msg)

        return text

    def _extract_activity_id(self, url: str) -> str | None:
        parsed = urlparse(url)
        query = parse_qs(parsed.query)
        values = query.get("id")
        if not values:
            return None

        activity_id = values[0].strip()
        return activity_id or None

    def _absolute_url(self, url: str) -> str:
        normalized = url.strip()
        if normalized.startswith(("http://", "https://")):
            return normalized

        return f"{self._base_url}/{normalized.lstrip('/')}"

    def _strip_due_suffix(self, title: str) -> str:
        normalized = title.strip()
        patterns = (
            r"\s+está en fecha de entrega$",
            r"\s+cierra$",
        )

        for pattern in patterns:
            normalized = re.sub(pattern, "", normalized, flags=re.IGNORECASE)

        return normalized.strip()

    def _infer_status_from_timeline_item(self, *, title: str, action_text: str | None) -> str:
        combined = f"{title} {action_text or ''}".casefold()

        if "añadir envío" in combined or "pending" in combined:
            return "sin entregar"

        if "comenzar el examen ya" in combined:
            return "sin entregar"

        if "overdue" in combined or "vencid" in combined or "late" in combined:
            return "vencida"

        return "sin entregar"

    def _parse_spanish_datetime(self, *, date_text: str, time_text: str) -> datetime | None:
        if not date_text.strip() or not time_text.strip():
            return None

        date_match = re.search(
            r"(\d{1,2})\s+de\s+([a-záéíóúñ]+)\s+de\s+(\d{4})",
            date_text,
            flags=re.IGNORECASE,
        )
        time_match = re.search(r"(\d{1,2}):(\d{2})", time_text)

        if date_match is None or time_match is None:
            return None

        day = int(date_match.group(1))
        month = self._spanish_month_to_number(date_match.group(2))
        year = int(date_match.group(3))
        hour = int(time_match.group(1))
        minute = int(time_match.group(2))

        return datetime(year, month, day, hour, minute)

    def _parse_full_spanish_datetime(self, value: str) -> datetime | None:
        match = re.search(
            r"(\d{1,2})\s+de\s+([a-záéíóúñ]+)\s+de\s+(\d{4}),\s+(\d{1,2}):(\d{2})",
            value,
            flags=re.IGNORECASE,
        )
        if match is None:
            return None

        day = int(match.group(1))
        month = self._spanish_month_to_number(match.group(2))
        year = int(match.group(3))
        hour = int(match.group(4))
        minute = int(match.group(5))

        return datetime(year, month, day, hour, minute)

    def _spanish_month_to_number(self, month_name: str) -> int:
        month_map = {
            "enero": 1,
            "febrero": 2,
            "marzo": 3,
            "abril": 4,
            "mayo": 5,
            "junio": 6,
        }