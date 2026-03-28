from datetime import datetime

from app.application.services.prompt_builder import PromptBuilder
from app.domain.enums import TaskStatus
from app.domain.models.task import Task


def _task(*, due_at: datetime | None = None) -> Task:
    return Task(
        id="task-1",
        course_name="Algorithms",
        title="Homework 2",
        description_text="Solve all exercises with clear intermediate steps.",
        due_at=due_at,
        status=TaskStatus.PENDING,
        url="https://example.edu/moodle/task-1",
    )


def test_build_task_help_prompt_contains_required_sections() -> None:
    builder = PromptBuilder()
    prompt = builder.build_task_help_prompt(task=_task(due_at=datetime(2026, 4, 1, 12, 30)))

    assert "You are an academic task assistant." in prompt
    assert "1. Summary" in prompt
    assert "2. Deliverable" in prompt
    assert "3. Steps" in prompt
    assert "4. Warnings" in prompt
    assert "5. Questions to clarify" in prompt
    assert "6. Final checklist" in prompt
    assert "Course: Algorithms" in prompt
    assert "Title: Homework 2" in prompt
    assert "Status: pending" in prompt
    assert "https://example.edu/moodle/task-1" in prompt


def test_build_task_help_prompt_uses_default_request_when_blank_question() -> None:
    builder = PromptBuilder()
    prompt = builder.build_task_help_prompt(task=_task(), user_question="   ")

    assert "Explain clearly what needs to be delivered" in prompt


def test_build_task_help_prompt_uses_custom_student_request() -> None:
    builder = PromptBuilder()
    prompt = builder.build_task_help_prompt(
        task=_task(),
        user_question="Give me a 30-minute plan and common mistakes.",
    )

    assert "Student request:\nGive me a 30-minute plan and common mistakes." in prompt


def test_build_task_help_prompt_handles_missing_due_date() -> None:
    builder = PromptBuilder()
    prompt = builder.build_task_help_prompt(task=_task(due_at=None))

    assert "Due at: No due date" in prompt
