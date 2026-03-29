from app.domain.models.task import Task


class PromptBuilder:
    """
    Build structured prompts for LLM-based task assistance.

    The prompt is intentionally deterministic and domain-specific so provider
    implementations can remain thin and focused on transport concerns.
    """

    def __init__(self, llm_language: str = "Spanish") -> None:
        self._llm_language = llm_language.strip() or "Spanish"

    def build_task_help_prompt(
        self,
        task: Task,
        user_question: str | None = None,
        *,
        include_step_metadata: bool = False,
    ) -> str:
        """
        Build the prompt used to request clear actionable help for a selected
        assignment.

        Args:
            task: The normalized task selected by the user.
            user_question: Optional extra user instruction to refine the help.

        Returns:
            A complete prompt string ready to be sent to an LLM provider.
        """
        normalized_question = self._normalize_user_question(user_question)

        sections = [
            self._build_role_section(),
            self._build_output_contract_section(include_step_metadata=include_step_metadata),
            self._build_task_context_section(task),
            self._build_user_request_section(normalized_question),
            self._build_behavior_rules_section(),
        ]

        return "\n\n".join(section for section in sections if section)

    def _normalize_user_question(self, user_question: str | None) -> str | None:
        if user_question is None:
            return None

        normalized = user_question.strip()
        return normalized or None

    def _build_role_section(self) -> str:
        return (
            "You are an academic task assistant. "
            "Your job is to help the student understand exactly what must be "
            "done and how to approach the task in a clear, practical way."
        )

    def _build_output_contract_section(self, *, include_step_metadata: bool) -> str:
        if include_step_metadata:
            return (
                "Return your answer as structured content with the following sections:\n"
                "1. Summary\n"
                "2. Deliverable\n"
                "3. Steps with metadata\n"
                "4. Warnings\n"
                "5. Questions to clarify\n"
                "6. Final checklist\n\n"
                "For each step, include:\n"
                "- description\n"
                "- estimated_minutes (integer 1 to 120)\n"
                "- difficulty (trivial|easy|moderate|hard)\n"
                "- is_minimal_first_step (true for only one step, ideally the first concrete action)"
            )

        return (
            "Return your answer as structured content with the following sections:\n"
            "1. Summary\n"
            "2. Deliverable\n"
            "3. Steps\n"
            "4. Warnings\n"
            "5. Questions to clarify\n"
            "6. Final checklist"
        )

    def _build_task_context_section(self, task: Task) -> str:
        description_text = task.description_text or "No description provided."

        due_at_text = task.due_at.isoformat() if task.due_at is not None else "No due date"

        return (
            "Task context:\n"
            f"- Course: {task.course_name}\n"
            f"- Title: {task.title}\n"
            f"- Due at: {due_at_text}\n"
            f"- Status: {task.status.value}\n"
            f"- URL: {task.url}\n"
            f"- Description:\n{description_text}"
        )

    def _build_user_request_section(self, user_question: str | None) -> str:
        if user_question is None:
            return (
                "Student request:\n"
                "Explain clearly what needs to be delivered and provide a practical "
                "step-by-step checklist to complete the task."
            )

        return f"Student request:\n{user_question}"

    def _build_behavior_rules_section(self) -> str:
        return (
            "Behavior rules:\n"
            "- Be concrete and concise.\n"
            "- Use simple language.\n"
            f"- Always answer in {self._llm_language}.\n"
            "- Do not invent requirements that are not present in the task.\n"
            "- If something is ambiguous, mention it under Questions to clarify.\n"
            "- Focus on what the student should actually do.\n"
            "- Make the Steps and Final checklist easy to follow."
        )