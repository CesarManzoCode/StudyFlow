from enum import StrEnum


class TaskStatus(StrEnum):
    """
    Canonical assignment status in the application domain.

    These values are intentionally normalized and independent from the exact
    wording returned by Moodle, so scraping/parsing layers can map platform-
    specific labels into a stable internal vocabulary.
    """

    PENDING = "pending"
    SUBMITTED = "submitted"
    OVERDUE = "overdue"
    UNKNOWN = "unknown"


class TaskPriority(StrEnum):
    """
    Priority classification derived exclusively from time remaining until the
    assignment deadline.
    """

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"