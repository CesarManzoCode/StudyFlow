import json
from asyncio import Lock
from datetime import datetime
from pathlib import Path

from pydantic import ValidationError

from app.config import BASE_DIR
from app.domain.models.task_state import TaskState
from app.domain.ports.state_repository import StateRepository


class PersistentTaskStateStore(StateRepository):
    """
    File-based persistent storage for task states.

    Stores all task states in a single JSON file (task_states.json) in the
    project's data directory. The file is automatically created if it doesn't exist.

    Thread-safe via asyncio.Lock.
    """

    def __init__(self, data_dir: Path | None = None) -> None:
        self.data_dir = data_dir or (BASE_DIR / "data")
        self.state_file = self.data_dir / "task_states.json"
        self._lock = Lock()

        # Ensure data directory exists
        self.data_dir.mkdir(parents=True, exist_ok=True)

    async def save(self, state: TaskState) -> None:
        """
        Persist a task state to JSON file.
        """
        async with self._lock:
            all_states = await self._load_all_from_disk()
            all_states[state.task_id] = state.model_dump(
                mode="json", serialize_as_any=True
            )
            await self._write_all_to_disk(all_states)

    async def get_by_task_id(self, task_id: str) -> TaskState | None:
        """
        Retrieve a task state by ID, or None if not found.
        """
        async with self._lock:
            all_states = await self._load_all_from_disk()
            state_data = all_states.get(task_id)

            if not state_data:
                return None

            try:
                return TaskState(**state_data)
            except ValidationError as e:
                raise ValueError(
                    f"Failed to deserialize TaskState for task {task_id}: {e}"
                )

    async def get_all(self) -> dict[str, TaskState]:
        """
        Retrieve all stored task states as a dict keyed by task_id.
        """
        async with self._lock:
            all_states_data = await self._load_all_from_disk()
            result: dict[str, TaskState] = {}

            for task_id, state_data in all_states_data.items():
                try:
                    result[task_id] = TaskState(**state_data)
                except ValidationError as e:
                    raise ValueError(
                        f"Failed to deserialize TaskState for task {task_id}: {e}"
                    )

            return result

    async def delete(self, task_id: str) -> bool:
        """
        Delete a task state by ID. Returns True if deleted, False if not found.
        """
        async with self._lock:
            all_states = await self._load_all_from_disk()

            if task_id not in all_states:
                return False

            del all_states[task_id]
            await self._write_all_to_disk(all_states)
            return True

    async def clear_all(self) -> None:
        """
        Delete all stored task states.
        """
        async with self._lock:
            await self._write_all_to_disk({})

    async def _load_all_from_disk(self) -> dict:
        """
        Load all task states from disk. Returns empty dict if file doesn't exist.
        """
        if not self.state_file.exists():
            return {}

        try:
            with open(self.state_file, "r") as f:
                content = f.read().strip()
                if not content:
                    return {}
                return json.loads(content)
        except (json.JSONDecodeError, IOError) as e:
            raise ValueError(f"Failed to load task states from {self.state_file}: {e}")

    async def _write_all_to_disk(self, all_states: dict) -> None:
        """
        Write all task states to disk as JSON.
        """
        try:
            with open(self.state_file, "w") as f:
                json.dump(all_states, f, indent=2, default=str)
        except IOError as e:
            raise ValueError(f"Failed to write task states to {self.state_file}: {e}")
