class StudyFlowError(Exception):
    """
    Base application exception.

    All custom exceptions in the project should inherit from this type so the
    application can handle known failures in a consistent way.
    """


class ConfigurationError(StudyFlowError):
    """
    Raised when the application configuration is invalid or incomplete.
    """


class TaskNotFoundError(StudyFlowError):
    """
    Raised when a requested task does not exist in the current in-memory state.
    """


class MoodleScrapingError(StudyFlowError):
    """
    Raised when Moodle data cannot be fetched or normalized successfully.
    """


class MoodleAuthenticationError(MoodleScrapingError):
    """
    Raised when Moodle authentication fails due to invalid credentials or an
    unexpected login outcome.
    """


class LlmProviderError(StudyFlowError):
    """
    Raised when an LLM provider request fails or returns an unusable result.
    """


class InvalidLlmResponseError(LlmProviderError):
    """
    Raised when an LLM provider responds successfully but the payload cannot be
    normalized into the expected structured checklist format.
    """