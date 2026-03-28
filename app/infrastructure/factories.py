from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta

from app.application.services.prompt_builder import PromptBuilder
from app.application.services.task_priority_service import TaskPriorityService
from app.application.use_cases.generate_task_help import GenerateTaskHelpUseCase
from app.application.use_cases.get_task_detail import GetTaskDetailUseCase
from app.application.use_cases.list_tasks import ListTasksUseCase
from app.application.use_cases.save_settings import SaveSettingsUseCase
from app.application.use_cases.sync_tasks import SyncTasksUseCase
from app.application.use_cases.validate_provider import ValidateProviderUseCase
from app.config import Settings, get_settings
from app.domain.enums import TaskStatus
from app.domain.models.checklist import ChecklistResponse
from app.domain.models.task import Task
from app.domain.ports.llm_client import LlmClient
from app.domain.ports.moodle_client import MoodleClient
from app.domain.ports.task_repository import TaskRepository
from app.infrastructure.cache.in_memory_task_store import InMemoryTaskStore


logger = logging.getLogger(__name__)


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

    settings: Settings

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
    save_settings: SaveSettingsUseCase
    validate_provider: ValidateProviderUseCase


# =========================================================
# ROOT FACTORY
# =========================================================

def build_app_container(settings: Settings | None = None) -> AppContainer:
    """
    Compose the entire application graph.

    This is the single place where:
    - infrastructure is instantiated
    - providers are selected
    - dependencies are wired together
    """

    resolved_settings = settings or get_settings()

    # ---------------------------
    # Infrastructure
    # ---------------------------
    task_repository = InMemoryTaskStore()
    moodle_client = _build_moodle_client(resolved_settings)
    llm_client = _build_llm_client(resolved_settings)

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

    save_settings = SaveSettingsUseCase()
    validate_provider = ValidateProviderUseCase()

    return AppContainer(
        settings=resolved_settings,
        task_repository=task_repository,
        moodle_client=moodle_client,
        llm_client=llm_client,
        task_priority_service=task_priority_service,
        prompt_builder=prompt_builder,
        list_tasks=list_tasks,
        get_task_detail=get_task_detail,
        sync_tasks=sync_tasks,
        generate_task_help=generate_task_help,
        save_settings=save_settings,
        validate_provider=validate_provider,
    )


# =========================================================
# LLM FACTORY
# =========================================================

def _build_moodle_client(settings: Settings) -> MoodleClient:
    if _should_use_demo_moodle(settings):
        logger.info("Using demo Moodle client.")
        return _DemoMoodleClient(base_url=settings.moodle_base_url)

    try:
        from app.infrastructure.moodle.playwright_client import PlaywrightMoodleClient
    except ModuleNotFoundError:
        logger.warning("Playwright is not installed; falling back to the demo Moodle client.")
        return _DemoMoodleClient(base_url=settings.moodle_base_url)

    from app.infrastructure.moodle.parser import MoodleTaskParser

    parser = MoodleTaskParser()
    return PlaywrightMoodleClient(
        base_url=settings.moodle_base_url,
        username=settings.moodle_username,
        password=settings.moodle_password,
        parser=parser,
        headless=settings.moodle_headless,
    )


def _build_llm_client(settings: Settings) -> LlmClient:
    provider = settings.llm_provider

    if settings.llm_model == "demo-checklist":
        logger.info("Using demo LLM client.")
        return _DemoLlmClient(provider=provider, model=settings.llm_model)

    if provider == "ollama":
        if not settings.llm_base_url:
            logger.warning("Ollama base URL missing; falling back to the demo LLM client.")
            return _DemoLlmClient(provider=provider, model=settings.llm_model)

        try:
            from app.infrastructure.llm.ollama_client import OllamaClient
        except ModuleNotFoundError:
            logger.warning("httpx is not installed; falling back to the demo LLM client.")
            return _DemoLlmClient(provider=provider, model=settings.llm_model)

        return OllamaClient(base_url=settings.llm_base_url, model=settings.llm_model)

    if provider == "openai":
        if not settings.llm_api_key:
            logger.warning("OpenAI API key missing; falling back to the demo LLM client.")
            return _DemoLlmClient(provider=provider, model=settings.llm_model)

        try:
            from app.infrastructure.llm.openai_client import OpenAIClient
        except ModuleNotFoundError:
            logger.warning("OpenAI SDK is not installed; falling back to the demo LLM client.")
            return _DemoLlmClient(provider=provider, model=settings.llm_model)

        return OpenAIClient(api_key=settings.llm_api_key, model=settings.llm_model)

    if provider == "groq":
        if not settings.llm_api_key:
            logger.warning("Groq API key missing; falling back to the demo LLM client.")
            return _DemoLlmClient(provider=provider, model=settings.llm_model)

        try:
            from app.infrastructure.llm.groq_client import GroqClient
        except ModuleNotFoundError:
            logger.warning("OpenAI SDK is not installed; falling back to the demo LLM client.")
            return _DemoLlmClient(provider=provider, model=settings.llm_model)

        return GroqClient(api_key=settings.llm_api_key, model=settings.llm_model)

    if provider == "anthropic":
        if not settings.llm_api_key:
            logger.warning("Anthropic API key missing; falling back to the demo LLM client.")
            return _DemoLlmClient(provider=provider, model=settings.llm_model)

        try:
            from app.infrastructure.llm.anthropic_client import AnthropicClient
        except ModuleNotFoundError:
            logger.warning("Anthropic SDK is not installed; falling back to the demo LLM client.")
            return _DemoLlmClient(provider=provider, model=settings.llm_model)

        return AnthropicClient(api_key=settings.llm_api_key, model=settings.llm_model)

    logger.warning("Unsupported provider '%s'; falling back to the demo LLM client.", provider)
    return _DemoLlmClient(provider=provider, model=settings.llm_model)


def _should_use_demo_moodle(settings: Settings) -> bool:
    return "example.edu" in settings.moodle_base_url or settings.moodle_username.startswith("demo.")


class _DemoMoodleClient(MoodleClient):
    def __init__(self, *, base_url: str) -> None:
        self._base_url = base_url.rstrip("/")

    async def fetch_tasks(self) -> list[Task]:
        now = datetime.now().replace(second=0, microsecond=0)
        return [
            Task(
                id="demo-essay-draft",
                title="Critical Essay Draft",
                course_name="Academic Writing",
                description_text="Prepare a first draft arguing your thesis with three supporting points.",
                due_at=now + timedelta(days=1, hours=4),
                status=TaskStatus.PENDING,
                url=f"{self._base_url}/mod/assign/view.php?id=demo-essay-draft",
            ),
            Task(
                id="demo-research-log",
                title="Research Log Update",
                course_name="History of Science",
                description_text="Summarize the two sources you selected and explain why they are relevant.",
                due_at=now + timedelta(days=3),
                status=TaskStatus.PENDING,
                url=f"{self._base_url}/mod/assign/view.php?id=demo-research-log",
            ),
            Task(
                id="demo-problem-set",
                title="Problem Set 4",
                course_name="Applied Mathematics",
                description_text="Solve the assigned exercises and show the intermediate steps for each answer.",
                due_at=now + timedelta(days=6, hours=2),
                status=TaskStatus.PENDING,
                url=f"{self._base_url}/mod/assign/view.php?id=demo-problem-set",
            ),
        ]

    async def fetch_task_detail(self, task_url: str) -> Task:
        for task in await self.fetch_tasks():
            if task.url == task_url or task.id in task_url:
                return task.model_copy(
                    update={
                        "description_text": (
                            f"{task.description_text}\n\n"
                            "This task is coming from StudyFlow demo mode so you can verify "
                            "the full UI and AI flow without live Moodle credentials."
                        ),
                        "description_html": (
                            f"<p>{task.description_text}</p>"
                            "<p>This task is coming from <strong>StudyFlow demo mode</strong> "
                            "so you can verify the full UI and AI flow without live Moodle "
                            "credentials.</p>"
                        ),
                    }
                )

        return Task(
            id="demo-task",
            title="Demo Task",
            course_name="General Studies",
            description_text="Open the settings page to connect a real Moodle instance.",
            due_at=None,
            status=TaskStatus.PENDING,
            url=task_url or f"{self._base_url}/mod/assign/view.php?id=demo-task",
        )


class _DemoLlmClient(LlmClient):
    def __init__(self, *, provider: str, model: str) -> None:
        self._provider = provider
        self._model = model

    async def generate_checklist(
        self,
        task: Task,
        user_question: str | None = None,
    ) -> ChecklistResponse:
        due_at_text = task.due_at.strftime("%Y-%m-%d %H:%M") if task.due_at else "No due date"
        custom_focus = "Focus on the standard assignment requirements."
        if user_question and "Student request:" in user_question:
            custom_focus = "Focus on the student's latest request and the assignment requirements."

        return ChecklistResponse(
            summary=(
                f"{task.title} for {task.course_name} is currently tracked through the "
                f"{self._provider} provider configuration."
            ),
            deliverable=(
                f"Submit the requested work for '{task.title}' before {due_at_text}."
            ),
            steps=[
                "Read the full assignment description and highlight the required deliverable.",
                "Break the work into one draft or problem-solving pass plus one review pass.",
                custom_focus,
                "Complete the task and compare the result against the final checklist before submitting.",
            ],
            warnings=[
                "Demo mode is active if you have not configured a live provider yet.",
                "Double-check platform-specific submission rules directly in Moodle before turning work in.",
            ],
            questions_to_clarify=[
                "Is there a grading rubric or attachment that changes the expected output?",
                "Does the task require a specific format, citation style, or file type?",
            ],
            final_checklist=[
                "I understand what must be delivered.",
                "I reviewed the due date and submission method.",
                "I completed the work and proofread it once.",
                "I verified the final output matches the assignment instructions.",
            ],
        )
