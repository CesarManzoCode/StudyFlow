from app.presentation.forms.ai_help_form import AiHelpForm
from app.presentation.forms.settings_form import SettingsForm


def test_ai_help_form_trims_and_normalizes_blank_to_none() -> None:
    filled = AiHelpForm.from_form(user_question="  Explain rubric  ")
    blank = AiHelpForm.from_form(user_question="   ")

    assert filled.user_question == "Explain rubric"
    assert blank.user_question is None


def test_settings_form_normalizes_text_and_optional_secrets() -> None:
    form = SettingsForm.from_form(
        moodle_base_url="  https://example.edu/moodle/  ",
        moodle_username="  student  ",
        llm_provider="  openai  ",
        llm_model="  gpt-5.4-nano  ",
        moodle_password="   ",
        llm_api_key=None,
        llm_base_url="  https://api.openai.com/v1  ",
    )

    assert form.moodle_base_url == "https://example.edu/moodle/"
    assert form.moodle_username == "student"
    assert form.llm_provider == "openai"
    assert form.llm_model == "gpt-5.4-nano"
    assert form.moodle_password is None
    assert form.llm_api_key is None
    assert form.llm_base_url == "https://api.openai.com/v1"
