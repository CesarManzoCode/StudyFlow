from __future__ import annotations

import json

import httpx

from app.domain.exceptions import InvalidLlmResponseError, LlmProviderError
from app.domain.models.checklist import ChecklistResponse
from app.domain.models.task import Task
from app.domain.models.task_step import EnhancedChecklistResponse
from app.domain.ports.llm_client import LlmClient
from app.infrastructure.llm.schemas import (
    ChecklistPayload,
    EnhancedChecklistPayload,
    fallback_enhanced_from_checklist,
)


class OllamaClient(LlmClient):
    """
    Ollama-backed implementation of the LLM client port.

    This adapter calls Ollama's local chat API and requests structured output
    using a JSON schema so the response can be validated deterministically.

    Note:
        The current domain port accepts `task` plus an optional `user_question`.
        At this stage of the architecture, the application layer may pass either
        a plain user refinement or a fully built prompt string in that argument.
        This client therefore treats `user_question` as the final user-facing
        prompt payload to send when provided.
    """

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        timeout_seconds: float = 60.0,
        keep_alive: str = "5m",
        temperature: float = 0.2,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model.strip()
        self._timeout_seconds = timeout_seconds
        self._keep_alive = keep_alive
        self._temperature = temperature

        if not self._model:
            msg = "Ollama model must not be empty."
            raise ValueError(msg)

        if self._timeout_seconds <= 0:
            msg = "timeout_seconds must be greater than zero."
            raise ValueError(msg)

    async def generate_checklist(
        self,
        task: Task,
        user_question: str | None = None,
    ) -> ChecklistResponse:
        """
        Generate a structured checklist for the selected task using Ollama.

        Args:
            task: The selected normalized task.
            user_question: Optional refined prompt payload. In the current
                architecture this may be either a plain user question or a full
                prompt built by the application layer.

        Returns:
            A validated domain ChecklistResponse.

        Raises:
            LlmProviderError:
                If the HTTP request fails or the provider response is malformed.
            InvalidLlmResponseError:
                If the provider returns content that cannot be validated into the
                expected checklist structure.
        """
        prompt = self._build_prompt(task=task, user_question=user_question)
        payload = self._build_request_payload(prompt=prompt)

        try:
            async with httpx.AsyncClient(
                base_url=self._base_url,
                timeout=self._timeout_seconds,
            ) as client:
                response = await client.post("/api/chat", json=payload)

            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = self._extract_http_error_detail(exc.response)
            msg = f"Ollama returned an HTTP error: {detail}"
            raise LlmProviderError(msg) from exc
        except httpx.HTTPError as exc:
            msg = f"Failed to communicate with Ollama: {exc!s}"
            raise LlmProviderError(msg) from exc

        try:
            response_data = response.json()
        except ValueError as exc:
            msg = "Ollama returned a non-JSON response."
            raise LlmProviderError(msg) from exc

        content = self._extract_message_content(response_data)

        try:
            validated_payload = ChecklistPayload.model_validate_json(content)
        except Exception as exc:
            msg = "Ollama response could not be validated as a checklist payload."
            raise InvalidLlmResponseError(msg) from exc

        return validated_payload.to_domain()

    async def generate_enhanced_checklist(
        self,
        task: Task,
        user_question: str | None = None,
    ) -> EnhancedChecklistResponse:
        """Generate checklist with LLM-provided step metadata."""
        prompt = self._build_prompt(task=task, user_question=user_question)
        payload = self._build_request_payload(prompt=prompt, enhanced=True)

        try:
            async with httpx.AsyncClient(
                base_url=self._base_url,
                timeout=self._timeout_seconds,
            ) as client:
                response = await client.post("/api/chat", json=payload)

            response.raise_for_status()
            response_data = response.json()
            content = self._extract_message_content(response_data)
            validated_payload = EnhancedChecklistPayload.model_validate_json(content)
            return validated_payload.to_domain()
        except Exception:
            checklist = await self.generate_checklist(task=task, user_question=user_question)
            return fallback_enhanced_from_checklist(checklist)

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

    def _build_request_payload(self, *, prompt: str, enhanced: bool = False) -> dict[str, object]:
        response_schema = (
            EnhancedChecklistPayload.model_json_schema()
            if enhanced
            else ChecklistPayload.model_json_schema()
        )

        return {
            "model": self._model,
            "stream": False,
            "keep_alive": self._keep_alive,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "format": response_schema,
            "options": {
                "temperature": self._temperature,
            },
        }

    def _extract_message_content(self, response_data: object) -> str:
        if not isinstance(response_data, dict):
            msg = "Ollama response payload must be a JSON object."
            raise LlmProviderError(msg)

        message = response_data.get("message")
        if not isinstance(message, dict):
            msg = "Ollama response does not contain a valid 'message' object."
            raise LlmProviderError(msg)

        content = message.get("content")
        if not isinstance(content, str):
            msg = "Ollama response does not contain textual message content."
            raise LlmProviderError(msg)

        normalized = content.strip()
        if not normalized:
            msg = "Ollama returned empty message content."
            raise LlmProviderError(msg)

        return normalized

    def _extract_http_error_detail(self, response: httpx.Response) -> str:
        try:
            payload = response.json()
        except ValueError:
            return f"{response.status_code} {response.text}".strip()

        if isinstance(payload, dict):
            error = payload.get("error")
            if isinstance(error, str) and error.strip():
                return error.strip()

            return json.dumps(payload, ensure_ascii=False)

        return f"{response.status_code} {response.text}".strip()