from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from app.application.services.prompt_builder import PromptBuilder
from app.application.use_cases.generate_task_help import GenerateTaskHelpUseCase
from app.domain.enums import TaskStatus
from app.domain.exceptions import TaskNotFoundError
from app.domain.models.checklist import ChecklistResponse
from app.domain.models.task import Task


@pytest.mark.asyncio
async def test_execute_refreshes_task_builds_prompt_and_calls_llm() -> None:
    stored_task = Task(
        id="task-1",
        course_name="Databases",
        title="Project draft",
        due_at=datetime(2026, 4, 4, 15, 0),
        status=TaskStatus.PENDING,
        url="https://example.edu/task-1",
    )
    refreshed_task = stored_task.model_copy(update={"description_text": "Detailed instructions"})
    checklist = ChecklistResponse(
        summary="Summary",
        deliverable="Deliverable",
        steps=["Step 1"],
        warnings=[],
        questions_to_clarify=[],
        final_checklist=["Done"],
    )

    repository = AsyncMock()
    repository.get_by_id = AsyncMock(return_value=stored_task)

    moodle_client = AsyncMock()
    moodle_client.fetch_task_detail = AsyncMock(return_value=refreshed_task)

    llm_client = AsyncMock()
    llm_client.generate_checklist = AsyncMock(return_value=checklist)

    prompt_builder = PromptBuilder()

    use_case = GenerateTaskHelpUseCase(
        task_repository=repository,
        moodle_client=moodle_client,
        llm_client=llm_client,
        prompt_builder=prompt_builder,
    )

    result = await use_case.execute(task_id="task-1", user_question="Focus on rubric")

    assert result == checklist
    repository.get_by_id.assert_awaited_once_with("task-1")
    moodle_client.fetch_task_detail.assert_awaited_once_with("https://example.edu/task-1")

    llm_client.generate_checklist.assert_awaited_once()
    call_kwargs = llm_client.generate_checklist.await_args.kwargs
    assert call_kwargs["task"] == refreshed_task
    assert "Focus on rubric" in call_kwargs["user_question"]
    assert "Return your answer as structured content" in call_kwargs["user_question"]


@pytest.mark.asyncio
async def test_execute_raises_task_not_found_when_repository_has_no_task() -> None:
    repository = AsyncMock()
    repository.get_by_id = AsyncMock(return_value=None)

    moodle_client = AsyncMock()
    llm_client = AsyncMock()

    use_case = GenerateTaskHelpUseCase(
        task_repository=repository,
        moodle_client=moodle_client,
        llm_client=llm_client,
        prompt_builder=PromptBuilder(),
    )

    with pytest.raises(TaskNotFoundError):
        await use_case.execute(task_id="missing")

    moodle_client.fetch_task_detail.assert_not_called()
    llm_client.generate_checklist.assert_not_called()
