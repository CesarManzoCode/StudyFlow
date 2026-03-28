from __future__ import annotations

from datetime import datetime

from app.domain.enums import TaskStatus
from app.domain.models.task import Task
from app.infrastructure.moodle.parser import RawTaskData


class MoodleTaskMapper:
    """
    Maps raw Moodle scraping data into domain Task models.
    """

    def map(self, raw: RawTaskData) -> Task:
        """
        Convert RawTaskData into a normalized Task.
        """
        return Task(
            id=self._normalize_id(raw.id),
            title=self._normalize_title(raw.title),
            course_name=self._normalize_course(raw.course_name),
            url=raw.url,
            description_text=self._extract_description(raw),
            due_at=raw.due_at,
            status=self._map_status(raw.submission_status_raw),
        )

    # =========================================================
    # FIELD NORMALIZATION
    # =========================================================

    def _normalize_id(self, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Task id cannot be empty.")
        return normalized

    def _normalize_title(self, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            return "Untitled task"
        return normalized

    def _normalize_course(self, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            return "Unknown course"
        return normalized

    def _extract_description(self, raw: RawTaskData) -> str | None:
        """
        Prefer plain text if already parsed, fallback to HTML stripping.
        """
        if raw.description_text:
            return raw.description_text.strip()

        if raw.description_html:
            return self._strip_html(raw.description_html)

        return None

    # =========================================================
    # STATUS MAPPING
    # =========================================================

    def _map_status(self, raw_status: str | None) -> TaskStatus:
        """
        Convert Moodle-specific status text into domain enum.
        """
        if raw_status is None:
            return TaskStatus.UNKNOWN

        value = raw_status.strip().casefold()

        # --- common Moodle values (Spanish / English mix) ---
        if "sin intento" in value:
            return TaskStatus.PENDING

        if "no entregado" in value:
            return TaskStatus.PENDING

        if "submitted" in value or "entregado" in value:
            return TaskStatus.SUBMITTED

        if "late" in value or "retras" in value:
            return TaskStatus.LATE

        if "graded" in value or "calificado" in value:
            return TaskStatus.GRADED

        return TaskStatus.UNKNOWN

    # =========================================================
    # HELPERS
    # =========================================================

    def _strip_html(self, html: str) -> str:
        """
        Very simple HTML stripping for fallback cases.

        Note:
            This is intentionally lightweight to avoid external dependencies.
        """
        import re

        text = re.sub(r"<[^>]+>", "", html)
        return text.strip()