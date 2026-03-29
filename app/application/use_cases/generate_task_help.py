from app.application.services.prompt_builder import PromptBuilder
from app.domain.models.checklist import ChecklistResponse
from app.domain.models.task_step import EnhancedChecklistResponse
from app.domain.ports.llm_client import LlmClient
from app.domain.ports.moodle_client import MoodleClient
from app.domain.ports.task_repository import TaskRepository


class GenerateTaskHelpUseCase:
    """
    Generate structured AI help for a selected task.

    The use case refreshes the selected task from Moodle before sending it to
    the LLM so the generated guidance uses the most complete task detail
    available at request time.
    """

    def __init__(
        self,
        task_repository: TaskRepository,
        moodle_client: MoodleClient,
        llm_client: LlmClient,
        prompt_builder: PromptBuilder,
    ) -> None:
        self._task_repository = task_repository
        self._moodle_client = moodle_client
        self._llm_client = llm_client
        self._prompt_builder = prompt_builder

    async def execute(
        self,
        task_id: str,
        user_question: str | None = None,
    ) -> ChecklistResponse:
        """
        Generate structured help for the selected task.

        Args:
            task_id: The normalized task identifier.
            user_question: Optional extra user question to refine the help.

        Returns:
            A structured checklist response.

        Raises:
            TaskNotFoundError:
                If the task does not exist in the current in-memory snapshot.
            MoodleAuthenticationError:
                If Moodle authentication fails while fetching the task detail.
            MoodleScrapingError:
                If Moodle task detail cannot be fetched or normalized.
            LlmProviderError:
                If the provider request fails or returns unusable content.
            InvalidLlmResponseError:
                If the provider response cannot be normalized.
        """
        task = await self._get_existing_task(task_id=task_id)
        refreshed_task = await self._moodle_client.fetch_task_detail(task.url)

        prompt = self._prompt_builder.build_task_help_prompt(
            task=refreshed_task,
            user_question=user_question,
        )

        return await self._llm_client.generate_checklist(
            task=refreshed_task,
            user_question=prompt,
        )

    async def execute_enhanced(
        self,
        task_id: str,
        user_question: str | None = None,
    ) -> EnhancedChecklistResponse:
        """
        Generate enhanced structured help with per-step effort metadata.
        """
        task = await self._get_existing_task(task_id=task_id)
        refreshed_task = await self._moodle_client.fetch_task_detail(task.url)

        prompt = self._prompt_builder.build_task_help_prompt(
            task=refreshed_task,
            user_question=user_question,
            include_step_metadata=True,
        )

        return await self._llm_client.generate_enhanced_checklist(
            task=refreshed_task,
            user_question=prompt,
        )

    async def _get_existing_task(self, task_id: str):
        task = await self._task_repository.get_by_id(task_id)
        if task is None:
            from app.domain.exceptions import TaskNotFoundError

            msg = f"Task with id '{task_id}' was not found."
            raise TaskNotFoundError(msg)

        return task