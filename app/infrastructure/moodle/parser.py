from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from html import unescape
from typing import Final
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from app.domain.enums import TaskStatus
from app.domain.exceptions import MoodleScrapingError
from app.domain.models.task import Task


@dataclass(frozen=True, slots=True)
class RawTaskData:
    """
    Raw normalized scraping payload before conversion into the Task domain model.

    This object represents the boundary between browser extraction and domain
    normalization. Values may still be incomplete or partially untrusted.
    """

    id: str
    title: str
    course_name: str
    url: str
    description_html: str | None = None
    due_at: datetime | None = None
    submission_status_raw: str | None = None


_STATUS_MAPPING: Final[dict[str, TaskStatus]] = {
    "not submitted": TaskStatus.PENDING,
    "no enviado": TaskStatus.PENDING,
    "sin entregar": TaskStatus.PENDING,
    "submitted for grading": TaskStatus.SUBMITTED,
    "submitted": TaskStatus.SUBMITTED,
    "enviado para calificación": TaskStatus.SUBMITTED,
    "enviado para calificar": TaskStatus.SUBMITTED,
    "done": TaskStatus.SUBMITTED,
    "graded": TaskStatus.SUBMITTED,
    "overdue": TaskStatus.OVERDUE,
    "late": TaskStatus.OVERDUE,
    "retrasada": TaskStatus.OVERDUE,
    "vencida": TaskStatus.OVERDUE,
    "atrasada": TaskStatus.OVERDUE,
}


class MoodleTaskParser:
    """
    Convert raw scraped Moodle task payloads into normalized Task domain models.
    """

    def parse_many(self, raw_tasks: list[RawTaskData]) -> list[Task]:
        """
        Parse multiple raw tasks into domain entities.

        Raises:
            MoodleScrapingError:
                If any task cannot be normalized safely.
        """
        return [self.parse_one(raw_task) for raw_task in raw_tasks]

    def parse_one(self, raw_task: RawTaskData) -> Task:
        """
        Parse a single raw task payload into a normalized Task entity.
        """
        task_id = self._require_non_empty(raw_task.id, field_name="id")
        title = self._require_non_empty(raw_task.title, field_name="title")
        course_name = self._require_non_empty(raw_task.course_name, field_name="course_name")
        url = self._require_non_empty(raw_task.url, field_name="url")

        description_html = self._normalize_optional_text(raw_task.description_html)
        description_text = self._html_to_text(description_html) if description_html else None
        status = self._normalize_status(raw_task.submission_status_raw)

        return Task(
            id=task_id,
            title=title,
            course_name=course_name,
            url=url,
            description_html=description_html,
            description_text=description_text,
            due_at=raw_task.due_at,
            status=status,
        )

    def build_raw_task(
        self,
        *,
        id: str,
        title: str,
        course_name: str,
        url: str,
        description_html: str | None = None,
        due_at: datetime | None = None,
        submission_status_raw: str | None = None,
        base_url: str | None = None,
    ) -> RawTaskData:
        """
        Helper for constructing RawTaskData with URL normalization.

        This is useful for infrastructure code that extracts relative URLs from
        Moodle pages and wants to normalize them before creating domain models.
        """
        normalized_url = self._normalize_url(url=url, base_url=base_url)

        return RawTaskData(
            id=id,
            title=title,
            course_name=course_name,
            url=normalized_url,
            description_html=description_html,
            due_at=due_at,
            submission_status_raw=submission_status_raw,
        )

    def _normalize_status(self, raw_status: str | None) -> TaskStatus:
        if raw_status is None:
            return TaskStatus.UNKNOWN

        normalized = self._normalize_optional_text(raw_status)
        if normalized is None:
            return TaskStatus.UNKNOWN

        key = normalized.casefold()
        return _STATUS_MAPPING.get(key, TaskStatus.UNKNOWN)

    def _normalize_url(self, *, url: str, base_url: str | None) -> str:
        normalized_url = self._require_non_empty(url, field_name="url")

        if normalized_url.startswith(("http://", "https://")):
            return normalized_url

        if base_url is None:
            msg = "Relative Moodle URL cannot be normalized without a base URL."
            raise MoodleScrapingError(msg)

        return urljoin(base_url.rstrip("/") + "/", normalized_url.lstrip("/"))

    def _require_non_empty(self, value: str, *, field_name: str) -> str:
        normalized = value.strip()
        if not normalized:
            msg = f"Raw Moodle task field '{field_name}' must not be empty."
            raise MoodleScrapingError(msg)
        return normalized

    def _normalize_optional_text(self, value: str | None) -> str | None:
        if value is None:
            return None

        normalized = unescape(value).strip()
        return normalized or None

    def _html_to_text(self, html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(separator="\n", strip=True)
        normalized_lines = [line.strip() for line in text.splitlines() if line.strip()]
        return "\n".join(normalized_lines)