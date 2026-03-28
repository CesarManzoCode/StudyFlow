from __future__ import annotations

import json

from anthropic import (
    APIConnectionError,
    APIError,
    APITimeoutError,
    AsyncAnthropic,
    RateLimitError,
)

from app.domain.exceptions import InvalidLlmResponseError, LlmProviderError
from app.domain.models.checklist import ChecklistResponse
from app.domain.models.task import Task
from app.domain.ports.llm_client import LlmClient
from app.infrastructure.llm.schemas import ChecklistPayload


class AnthropicClient(LlmClient):
    """
    Anthropic-backed implementation of the LLM client port.

    This adapter uses Anthropic's Messages API and requests JSON-only output.
    The JSON is then validated against the infrastructure schema before being
    converted into the domain model.

    Note:
        The current domain port accepts `task` plus an optional `user_question`.
        In the current architecture, the application layer may pass either a
        plain refinement from the user or a fully built prompt string in that
        argument. This adapter therefore treats `user_question` as the final
        user-facing prompt payload when it is present.
    """

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        timeout_seconds: float = 60.0,
        max_tokens: int = 2000,
        temperature: float = 0.2,
    ) -> None:
        normalized_api_key = api_key.strip()
        normalized_model = model.strip()

        if not normalized_api_key:
            msg = "Anthropic API key must not be empty."
            raise ValueError(msg)

        if not normalized_model:
            msg = "Anthropic model must not be empty."
            raise ValueError(msg)

        if timeout_seconds <= 0:
            msg = "timeout_seconds must be greater than zero."
            raise ValueError(msg)

        if max_tokens <= 0:
            msg = "max_tokens must be greater than zero."
            raise ValueError(msg)

        self._model = normalized_model
        self._max_tokens = max_tokens
        self._temperature = temperature
        self._client = AsyncAnthropic(
            api_key=normalized_api_key,
            timeout=timeout_seconds,
        )

    async def generate_checklist(
        self,
        task: Task,
        user_question: str | None = None,
    ) -> ChecklistResponse:
        """
        Generate a structured checklist for the selected task using Anthropic.

        Args:
            task: The selected normalized task.
            user_question: Optional refined prompt payload. In the current
                architecture this may be either a plain user question or a full
                prompt built by the application layer.

        Returns:
            A validated domain ChecklistResponse.

        Raises:
            LlmProviderError:
                If the provider request fails or the response is malformed.
            InvalidLlmResponseError:
                If the provider returns content that cannot be validated into the
                expected checklist structure.
        """
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(task=task, user_question=user_question)

        try:
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=self._max_tokens,
                temperature=self._temperature,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": user_prompt,
                    }
                ],
            )
        except (APIConnectionError, APITimeoutError, RateLimitError, APIError) as exc:
            msg = f"Failed to communicate with Anthropic: {exc!s}"
            raise LlmProviderError(msg) from exc
        except Exception as exc:
            msg = f"Unexpected Anthropic client error: {exc!s}"
            raise LlmProviderError(msg) from exc

        content = self._extract_text_content(response)

        try:
            parsed_json = json.loads(content)
        except json.JSONDecodeError as exc:
            msg = "Anthropic response was not valid JSON."
            raise InvalidLlmResponseError(msg) from exc

        try:
            validated_payload = ChecklistPayload.model_validate(parsed_json)
        except Exception as exc:
            msg = "Anthropic response could not be validated as a checklist payload."
            raise InvalidLlmResponseError(msg) from exc

        return validated_payload.to_domain()

    def _build_system_prompt(self) -> str:
        schema_json = json.dumps(ChecklistPayload.model_json_schema(), ensure_ascii=False, indent=2)

        return (
            "You are an academic task assistant.\n"
            "You must respond with valid JSON only.\n"
            "Do not include markdown fences.\n"
            "Do not include explanations before or after the JSON.\n"
            "The JSON must conform to this schema:\n"
            f"{schema_json}"
        )

    def _build_user_prompt(self, *, task: Task, user_question: str | None) -> str:
        normalized_question = (user_question or "").strip()
        if normalized_question:
            return normalized_question

        description = task.description_text or "No description provided."
        due_at = task.due_at.isoformat() if task.due_at is not None else "No due date"

        return (
            "Task context:\n"
            f"- Course: {task.course_name}\n"
            f"- Title: {task.title}\n"
            f"- Due at: {due_at}\n"
            f"- Status: {task.status.value}\n"
            f"- URL: {task.url}\n"
            f"- Description:\n{description}\n\n"
            "Student request:\n"
            "Explain clearly what needs to be delivered and provide a practical "
            "step-by-step checklist to complete the task.\n\n"
            "Return JSON only."
        )

    def _extract_text_content(self, response: object) -> str:
        """
        Extract concatenated text blocks from an Anthropic Messages response.
        """
        content_blocks = getattr(response, "content", None)
        if not isinstance(content_blocks, list):
            msg = "Anthropic response did not contain a valid content list."
            raise LlmProviderError(msg)

        text_parts: list[str] = []

        for block in content_blocks:
            block_type = getattr(block, "type", None)
            if block_type != "text":
                continue

            text = getattr(block, "text", None)
            if isinstance(text, str) and text.strip():
                text_parts.append(text.strip())

        if not text_parts:
            msg = "Anthropic response did not contain textual output."
            raise LlmProviderError(msg)

        return "\n".join(text_parts)