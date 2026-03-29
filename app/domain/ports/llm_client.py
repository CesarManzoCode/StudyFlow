from typing import Protocol

from app.domain.models.checklist import ChecklistResponse
from app.domain.models.task import Task
from app.domain.models.task_step import EnhancedChecklistResponse


class LlmClient(Protocol):
    """
    Contract for generating structured AI guidance for a selected task.

    Implementations are responsible for talking to a concrete provider and
    normalizing the result into the domain-level ChecklistResponse model.
    """

    async def generate_checklist(
        self,
        task: Task,
        user_question: str | None = None,
    ) -> ChecklistResponse:
        """
        Generate a structured checklist response for the given task.

        Args:
            task: The normalized task selected by the user.
            user_question: Optional extra user prompt to refine the requested
                guidance for the selected task.

        Returns:
            A normalized structured checklist response.

        Raises:
            LlmProviderError:
                If the provider call fails or returns an unusable result.
            InvalidLlmResponseError:
                If the provider returns data that cannot be normalized into the
                expected domain output.
        """

    async def generate_enhanced_checklist(
        self,
        task: Task,
        user_question: str | None = None,
    ) -> EnhancedChecklistResponse:
        """
        Generate structured checklist response with per-step metadata.

        Args:
            task: The normalized task selected by the user.
            user_question: Optional extra user prompt to refine the requested
                guidance for the selected task.

        Returns:
            A normalized enhanced checklist response that includes step-level
            estimated time, difficulty, and minimal-first-step signal.
        """