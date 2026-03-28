import pytest

from app.application.use_cases.validate_provider import ValidateProviderUseCase
from app.domain.exceptions import InvalidLlmResponseError


@pytest.mark.asyncio
async def test_validate_provider_accepts_valid_ollama_config() -> None:
    use_case = ValidateProviderUseCase()

    await use_case.execute(
        provider="ollama",
        model="qwen3:latest",
        base_url="http://localhost:11434",
    )


@pytest.mark.asyncio
async def test_validate_provider_accepts_valid_cloud_config() -> None:
    use_case = ValidateProviderUseCase()

    await use_case.execute(
        provider="openai",
        model="gpt-5.4-nano",
        api_key="secret",
    )


@pytest.mark.asyncio
async def test_validate_provider_rejects_unsupported_provider() -> None:
    use_case = ValidateProviderUseCase()

    with pytest.raises(InvalidLlmResponseError, match="Unsupported LLM provider"):
        await use_case.execute(provider="foo", model="x")


@pytest.mark.asyncio
async def test_validate_provider_rejects_missing_model() -> None:
    use_case = ValidateProviderUseCase()

    with pytest.raises(InvalidLlmResponseError, match="LLM model is required"):
        await use_case.execute(provider="ollama", model="", base_url="http://localhost:11434")


@pytest.mark.asyncio
async def test_validate_provider_rejects_missing_ollama_base_url() -> None:
    use_case = ValidateProviderUseCase()

    with pytest.raises(InvalidLlmResponseError, match="Ollama requires a base URL"):
        await use_case.execute(provider="ollama", model="qwen3:latest", base_url="")


@pytest.mark.asyncio
async def test_validate_provider_rejects_missing_openai_api_key() -> None:
    use_case = ValidateProviderUseCase()

    with pytest.raises(InvalidLlmResponseError, match="Openai requires an API key"):
        await use_case.execute(provider="openai", model="gpt-5.4-nano", api_key="")
