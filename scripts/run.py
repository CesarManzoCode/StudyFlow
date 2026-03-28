from __future__ import annotations

import os
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
VENV_DIR = ROOT_DIR / ".venv"
VENV_PYTHON = ROOT_DIR / ".venv" / "bin" / "python"
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def _ensure_project_venv() -> None:
    if not VENV_PYTHON.exists():
        return

    if Path(sys.prefix).resolve() == VENV_DIR.resolve():
        return

    os.execv(str(VENV_PYTHON), [str(VENV_PYTHON), str(Path(__file__).resolve())])


def main() -> None:
    _ensure_project_venv()

    try:
        import uvicorn
    except ModuleNotFoundError as exc:
        msg = "uvicorn is not installed. Run `python -m pip install -e .` and try again."
        raise SystemExit(msg) from exc

    from app.config import get_settings

    settings = get_settings()

    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=False,
    )


if __name__ == "__main__":
    main()
