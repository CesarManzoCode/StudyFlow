from __future__ import annotations

import json

from openai import APIConnectionError, APIError, APITimeoutError, AsyncOpenAI, RateLimitError

from app.domain.exceptions import InvalidLlmResponseError, LlmProviderError
from app.domain.models.checklist import ChecklistResponse
from app.domain.models.task import Task
from app.domain.ports.llm_client import LlmClient
from app.infrastructure.llm.schemas import ChecklistPayload


class OpenAIClient(LlmClient):
    """
    OpenAI-backed implementation of the LLM client port.

    This adapter uses the Responses API with structured outputs via JSON Schema
    so provider output can be validated deterministically before conversion into
    the domain model.

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
    ) -> None:
        normalized_api_key = api_key.strip()
        normalized_model = model.strip()

        if not normalized_api_key:
            msg = "OpenAI API key must not be empty."
            raise ValueError(msg)

        if not normalized_model:
            msg = "OpenAI model must not be empty."
            raise ValueError(msg)

        if timeout_seconds <= 0:
            msg = "timeout_seconds must be greater than zero."
            raise ValueError(msg)

        self._model = normalized_model
        self._client = AsyncOpenAI(
            api_key=normalized_api_key,
            timeout=timeout_seconds,
        )

    async def generate_checklist(
        self,
        task: Task,
        user_question: str | None = None,
    ) -> ChecklistResponse:
        """
        Generate a structured checklist for the selected task using OpenAI.

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
        prompt = self._build_prompt(task=task, user_question=user_question)

        try:
            response = await self._client.responses.create(
                model=self._model,
                input=prompt,
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "checklist_payload",
                        "strict": True,
                        "schema": ChecklistPayload.model_json_schema(),
                    }
                },
            )
        except (APIConnectionError, APITimeoutError, RateLimitError, APIError) as exc:
            msg = f"Failed to communicate with OpenAI: {exc!s}"
            raise LlmProviderError(msg) from exc
        except Exception as exc:
            msg = f"Unexpected OpenAI client error: {exc!s}"
            raise LlmProviderError(msg) from exc

        content = self._extract_output_text(response)

        try:
            validated_payload = ChecklistPayload.model_validate_json(content)
        except Exception as exc:
            msg = "OpenAI response could not be validated as a checklist payload."
            raise InvalidLlmResponseError(msg) from exc

        return validated_payload.to_domain()

    def _build_prompt(self, *, task: Task, user_question: str | None) -> str:
        normalized_question = (user_question or "").strip()
        if normalized_question:
            return normalized_question

        description = task.description_text or "No description provided."
        due_at = task.due_at.isoformat() if task.due_at is not None else "No due date"

        return (
            "You are an academic task assistant.\n\n"
            "Return valid JSON only.\n"
            "The JSON must match the requested schema exactly.\n\n"
            "Task context:\n"
            f"- Course: {task.course_name}\n"
            f"- Title: {task.title}\n"
            f"- Due at: {due_at}\n"
            f"- Status: {task.status.value}\n"
            f"- URL: {task.url}\n"
            f"- Description:\n{description}\n\n"
            "Student request:\n"
            "Explain clearly what needs to be delivered and provide a practical "
            "step-by-step checklist to complete the task."
        )

    def _extract_output_text(self, response: object) -> str:
        """
        Extract textual content from a Responses API result.

        The OpenAI SDK exposes a convenient `output_text` attribute on Responses
        objects in current docs, so we prefer that when available.
        """
        output_text = getattr(response, "output_text", None)
        if isinstance(output_text, str):
            normalized = output_text.strip()
            if normalized:
                return normalized

        # Conservative fallback for unexpected SDK shapes.
        response_dict = self._coerce_response_to_dict(response)
        content = response_dict.get("output_text")
        if isinstance(content, str):
            normalized = content.strip()
            if normalized:
                return normalized

        msg = "OpenAI response did not contain textual output."
        raise LlmProviderError(msg)

    def _coerce_response_to_dict(self, response: object) -> dict[str, object]:
        if isinstance(response, dict):
            return response

        model_dump = getattr(response, "model_dump", None)
        if callable(model_dump):
            dumped = model_dump()
            if isinstance(dumped, dict):
                return dumped

        # Last-resort JSON conversion for SDK objects that may support it.
        to_json = getattr(response, "to_json", None)
        if callable(to_json):
            raw_json = to_json()
            if isinstance(raw_json, str):
                try:
                    parsed = json.loads(raw_json)
                except json.JSONDecodeError:
                    parsed = None
                if isinstance(parsed, dict):
                    return parsed

        return {}