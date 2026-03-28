from __future__ import annotations

from dataclasses import dataclass

from app.application.services.prompt_builder import PromptBuilder
from app.application.services.task_priority_service import TaskPriorityService
from app.application.use_cases.generate_task_help import GenerateTaskHelpUseCase
from app.application.use_cases.get_task_detail import GetTaskDetailUseCase
from app.application.use_cases.list_tasks import ListTasksUseCase
from app.application.use_cases.sync_tasks import SyncTasksUseCase
from app.domain.ports.llm_client import LlmClient
from app.domain.ports.moodle_client import MoodleClient
from app.domain.ports.task_repository import TaskRepository
from app.infrastructure.cache.in_memory_task_store import InMemoryTaskStore
from app.infrastructure.config.settings import get_settings
from app.infrastructure.llm.anthropic_client import AnthropicClient
from app.infrastructure.llm.groq_client import GroqClient
from app.infrastructure.llm.ollama_client import OllamaClient
from app.infrastructure.llm.openai_client import OpenAIClient
from app.infrastructure.moodle.parser import MoodleTaskParser
from app.infrastructure.moodle.playwright_client import PlaywrightMoodleClient


# =========================================================
# APP CONTAINER (estructura clara, sin magia)
# =========================================================

@dataclass(frozen=True, slots=True)
class AppContainer:
    """
    Explicit container holding all application dependencies.

    This replaces ad-hoc globals and makes wiring explicit,
    testable, and replaceable.
    """

    # core
    task_repository: TaskRepository
    moodle_client: MoodleClient
    llm_client: LlmClient

    # services
    task_priority_service: TaskPriorityService
    prompt_builder: PromptBuilder

    # use cases
    list_tasks: ListTasksUseCase
    get_task_detail: GetTaskDetailUseCase
    sync_tasks: SyncTasksUseCase
    generate_task_help: GenerateTaskHelpUseCase


# =========================================================
# ROOT FACTORY
# =========================================================

def build_app_container() -> AppContainer:
    """
    Compose the entire application graph.

    This is the single place where:
    - infrastructure is instantiated
    - providers are selected
    - dependencies are wired together
    """

    settings = get_settings()

    # ---------------------------
    # Infrastructure
    # ---------------------------
    task_repository = InMemoryTaskStore()
    parser = MoodleTaskParser()

    moodle_client = PlaywrightMoodleClient(
        base_url=settings.moodle_base_url,
        username=settings.moodle_username,
        password=settings.moodle_password,
        parser=parser,
        headless=settings.moodle_headless,
    )

    llm_client = _build_llm_client(settings)

    # ---------------------------
    # Services
    # ---------------------------
    task_priority_service = TaskPriorityService()
    prompt_builder = PromptBuilder()

    # ---------------------------
    # Use cases
    # ---------------------------
    list_tasks = ListTasksUseCase(
        task_repository=task_repository,
        task_priority_service=task_priority_service,
    )

    get_task_detail = GetTaskDetailUseCase(
        task_repository=task_repository,
    )

    sync_tasks = SyncTasksUseCase(
        moodle_client=moodle_client,
        task_repository=task_repository,
    )

    generate_task_help = GenerateTaskHelpUseCase(
        task_repository=task_repository,
        moodle_client=moodle_client,
        llm_client=llm_client,
        prompt_builder=prompt_builder,
    )

    return AppContainer(
        task_repository=task_repository,
        moodle_client=moodle_client,
        llm_client=llm_client,
        task_priority_service=task_priority_service,
        prompt_builder=prompt_builder,
        list_tasks=list_tasks,
        get_task_detail=get_task_detail,
        sync_tasks=sync_tasks,
        generate_task_help=generate_task_help,
    )


# =========================================================
# LLM FACTORY
# =========================================================

def _build_llm_client(settings) -> LlmClient:
    provider = settings.llm_provider

    if provider == "ollama":
        if not settings.llm_base_url:
            raise ValueError("LLM_BASE_URL is required for Ollama")

        return OllamaClient(
            base_url=settings.llm_base_url,
            model=settings.llm_model,
        )

    if provider == "openai":
        if not settings.llm_api_key:
            raise ValueError("LLM_API_KEY is required for OpenAI")

        return OpenAIClient(
            api_key=settings.llm_api_key,
            model=settings.llm_model,
        )

    if provider == "groq":
        if not settings.llm_api_key:
            raise ValueError("LLM_API_KEY is required for Groq")

        return GroqClient(
            api_key=settings.llm_api_key,
            model=settings.llm_model,
        )

    if provider == "anthropic":
        if not settings.llm_api_key:
            raise ValueError("LLM_API_KEY is required for Anthropic")

        return AnthropicClient(
            api_key=settings.llm_api_key,
            model=settings.llm_model,
        )

    raise ValueError(f"Unsupported LLM provider: {provider}")