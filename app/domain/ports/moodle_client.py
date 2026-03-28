from typing import Protocol

from app.domain.models.task import Task


class MoodleClient(Protocol):
    """
    Contract for fetching and normalizing task data from Moodle.

    Implementations are responsible for authentication, navigation, scraping,
    parsing, and normalization. Callers only depend on normalized domain tasks.
    """

    async def fetch_tasks(self) -> list[Task]:
        """
        Fetch the current task snapshot from Moodle.

        Returns:
            A normalized list of tasks obtained from Moodle.

        Raises:
            MoodleAuthenticationError:
                If login fails or the authenticated session cannot be created.
            MoodleScrapingError:
                If Moodle content cannot be fetched or normalized successfully.
        """

    async def fetch_task_detail(self, task_url: str) -> Task:
        """
        Fetch a single task detail page from Moodle and return a normalized task.

        Args:
            task_url: Absolute Moodle URL for the selected task.

        Returns:
            The normalized task detail.

        Raises:
            MoodleAuthenticationError:
                If login fails or the authenticated session cannot be created.
            MoodleScrapingError:
                If the task detail cannot be fetched or normalized successfully.
        """