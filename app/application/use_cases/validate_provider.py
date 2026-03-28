from __future__ import annotations

from app.domain.exceptions import InvalidLlmResponseError


class ValidateProviderUseCase:
    """
    Validate the provider-specific subset of submitted settings.
    """

    async def execute(
        self,
        *,
        provider: str,
        model: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> None:
        normalized_provider = provider.strip().casefold()
        normalized_model = (model or "").strip()
        normalized_api_key = (api_key or "").strip()
        normalized_base_url = (base_url or "").strip()

        supported_providers = {"ollama", "openai", "groq", "anthropic"}

        if normalized_provider not in supported_providers:
            msg = "Unsupported LLM provider."
            raise InvalidLlmResponseError(msg)

        if not normalized_model:
            msg = "LLM model is required."
            raise InvalidLlmResponseError(msg)

        if normalized_provider == "ollama" and not normalized_base_url:
            msg = "Ollama requires a base URL."
            raise InvalidLlmResponseError(msg)

        if normalized_provider in {"openai", "groq", "anthropic"} and not normalized_api_key:
            msg = f"{normalized_provider.title()} requires an API key."
            raise InvalidLlmResponseError(msg)
