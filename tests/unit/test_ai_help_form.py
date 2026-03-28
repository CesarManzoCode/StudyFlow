from app.presentation.forms.ai_help_form import AiHelpForm


def test_ai_help_form_none_when_no_input() -> None:
    form = AiHelpForm.from_form()
    assert form.user_question is None


def test_ai_help_form_normalizes_user_question() -> None:
    form = AiHelpForm.from_form(user_question="  build me a checklist  ")
    assert form.user_question == "build me a checklist"
