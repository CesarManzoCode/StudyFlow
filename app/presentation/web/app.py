from __future__ import annotations

from datetime import datetime

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.domain.exceptions import (
    InvalidLlmResponseError,
    LlmProviderError,
    MoodleAuthenticationError,
    MoodleScrapingError,
    TaskNotFoundError,
)
from app.infrastructure.factories import build_app_container

# =========================================================
# APP INIT
# =========================================================

app = FastAPI(title="StudyFlow")

container = build_app_container()

templates = Jinja2Templates(directory="app/presentation/web/templates")

app.mount(
    "/static",
    StaticFiles(directory="app/presentation/web/static"),
    name="static",
)


# =========================================================
# ERROR HANDLING
# =========================================================

def render_error(request: Request, message: str):
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "message": message,
        },
        status_code=500,
    )


# =========================================================
# ROUTES
# =========================================================

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """
    Dashboard principal.
    """
    try:
        tasks = await container.list_tasks.execute(now=datetime.now())
        last_sync = await container.task_repository.last_synced_at()

        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "tasks": tasks,
                "last_sync": last_sync,
            },
        )

    except Exception as exc:
        return render_error(request, f"Error loading tasks: {exc!s}")


@app.post("/sync")
async def sync():
    """
    Ejecuta scraping manual.
    """
    try:
        await container.sync_tasks.execute(synced_at=datetime.now())
        return RedirectResponse("/", status_code=303)

    except MoodleAuthenticationError as exc:
        return HTMLResponse(f"<h1>Login error</h1><p>{exc}</p>", status_code=401)

    except MoodleScrapingError as exc:
        return HTMLResponse(f"<h1>Scraping error</h1><p>{exc}</p>", status_code=500)

    except Exception as exc:
        return HTMLResponse(f"<h1>Unexpected error</h1><p>{exc}</p>", status_code=500)


@app.get("/task/{task_id}", response_class=HTMLResponse)
async def task_detail(request: Request, task_id: str):
    """
    Vista de una tarea específica.
    """
    try:
        task = await container.get_task_detail.execute(task_id)

        return templates.TemplateResponse(
            "task.html",
            {
                "request": request,
                "task": task,
                "checklist": None,
            },
        )

    except TaskNotFoundError:
        return HTMLResponse("<h1>Task not found</h1>", status_code=404)

    except Exception as exc:
        return render_error(request, f"Error loading task: {exc!s}")


@app.post("/task/{task_id}/help", response_class=HTMLResponse)
async def task_help(
    request: Request,
    task_id: str,
    user_question: str = Form(default=""),
):
    """
    Genera ayuda con IA para una tarea.
    """
    try:
        checklist = await container.generate_task_help.execute(
            task_id=task_id,
            user_question=user_question or None,
        )

        task = await container.get_task_detail.execute(task_id)

        return templates.TemplateResponse(
            "task.html",
            {
                "request": request,
                "task": task,
                "checklist": checklist,
            },
        )

    except TaskNotFoundError:
        return HTMLResponse("<h1>Task not found</h1>", status_code=404)

    except (LlmProviderError, InvalidLlmResponseError) as exc:
        return HTMLResponse(f"<h1>AI Error</h1><p>{exc}</p>", status_code=500)

    except MoodleAuthenticationError as exc:
        return HTMLResponse(f"<h1>Login error</h1><p>{exc}</p>", status_code=401)

    except MoodleScrapingError as exc:
        return HTMLResponse(f"<h1>Scraping error</h1><p>{exc}</p>", status_code=500)

    except Exception as exc:
        return HTMLResponse(f"<h1>Unexpected error</h1><p>{exc}</p>", status_code=500)