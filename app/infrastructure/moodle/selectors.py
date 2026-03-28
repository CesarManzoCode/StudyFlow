from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True, slots=True)
class MoodleLoginSelectors:
    """
    Selectors used during Moodle authentication.

    These selectors intentionally include conservative defaults commonly found
    in Moodle installations with standard username/password login forms.
    """

    username_input: str = 'input[name="username"]'
    password_input: str = 'input[name="password"]'
    submit_button: str = 'button[type="submit"], input[type="submit"]'
    login_error_candidates: tuple[str, ...] = (
        '[data-region="alert"]',
        '.alert-danger',
        '.loginerrors',
        '#loginerrormessage',
    )


@dataclass(frozen=True, slots=True)
class MoodleNavigationSelectors:
    """
    Selectors used to detect page readiness and locate relevant navigation areas.
    """

    page_ready_candidates: tuple[str, ...] = (
        "body",
        "#page",
        "#region-main",
        '[role="main"]',
    )
    main_content_candidates: tuple[str, ...] = (
        "#region-main",
        '[role="main"]',
        "main",
    )


@dataclass(frozen=True, slots=True)
class MoodleTaskSelectors:
    """
    Selectors for assignment/task discovery.

    These are intentionally modeled as candidate lists because Moodle markup can
    vary across themes and versions. The scraper should try them in order until
    it finds a match.
    """

    task_link_candidates: tuple[str, ...] = (
        'a[href*="/mod/assign/view.php"]',
        'a[href*="/course/view.php"]',
        'a[href*="/mod/"]',
    )
    task_container_candidates: tuple[str, ...] = (
        '[data-region="activity-information"]',
        ".activity-item",
        ".activity",
        "li.activity",
        ".assign",
    )
    title_candidates: tuple[str, ...] = (
        ".instancename",
        ".activityname a",
        "h1",
        "h2",
        "a",
    )
    course_name_candidates: tuple[str, ...] = (
        ".page-header-headings h1",
        ".page-context-header h1",
        ".header-heading",
        'a[href*="/course/view.php"]',
    )
    due_date_candidates: tuple[str, ...] = (
        'td:has-text("Due date") + td',
        'th:has-text("Due date") + td',
        'div:has-text("Due date")',
        'div:has-text("Fecha de entrega")',
        'td:has-text("Fecha de entrega") + td',
    )
    submission_status_candidates: tuple[str, ...] = (
        'td:has-text("Submission status") + td',
        'th:has-text("Submission status") + td',
        'div:has-text("Submission status")',
        'div:has-text("Estado de la entrega")',
        'td:has-text("Estado de la entrega") + td',
    )
    description_candidates: tuple[str, ...] = (
        ".activity-description",
        ".box.generalbox",
        "#intro",
        '[data-region="activity-description"]',
        "#region-main",
    )


LOGIN_SELECTORS: Final[MoodleLoginSelectors] = MoodleLoginSelectors()
NAVIGATION_SELECTORS: Final[MoodleNavigationSelectors] = MoodleNavigationSelectors()
TASK_SELECTORS: Final[MoodleTaskSelectors] = MoodleTaskSelectors()