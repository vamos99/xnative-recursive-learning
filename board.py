"""
board.py
---------

Maintains a simple project board for tracking tasks, their status and
optional metadata. A board is persisted to JSON on disk and can be
visualised or modified via the command line or through the Streamlit app.

Tasks on the board are represented as dictionaries with the following
fields:

``id``
    A unique integer identifier for the task.
``title``
    A short description of the task. This should succinctly describe
    what needs to be done (e.g. "Implement summariser module").
``status``
    The current state of the task. Allowed values are ``"todo"``,
    ``"in_progress"`` and ``"done"``.
``description``
    A longer, optional description providing additional context. This
    might include acceptance criteria or links to documentation.

You can extend the schema with additional fields if required. The
``ProjectBoard`` class exposes CRUD operations for tasks as well as a
simple summary.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Optional, Dict, Iterable


@dataclass
class Task:
    """Represents a single task on the project board."""

    id: int
    title: str
    status: str = "todo"
    description: str = ""

    def to_dict(self) -> Dict[str, any]:
        return asdict(self)


class ProjectBoard:
    """A minimalistic project board stored in JSON.

    Parameters
    ----------
    path : Path
        Location of the JSON file used for persisting tasks. If the file
        does not exist it will be created on first write.
    """

    def __init__(self, path: Path):
        self.path = path
        self.tasks: List[Task] = []
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text(encoding="utf-8"))
                self.tasks = [Task(**item) for item in data]
            except Exception as exc:
                print(f"[board] warning: failed to load board from {self.path}: {exc}")
                self.tasks = []
        else:
            self.tasks = []

    def _save(self) -> None:
        try:
            self.path.write_text(
                json.dumps([task.to_dict() for task in self.tasks], indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception as exc:
            print(f"[board] warning: failed to save board: {exc}")

    def _next_id(self) -> int:
        return (max((t.id for t in self.tasks), default=0) + 1)

    def add_task(self, title: str, description: str = "", status: str = "todo") -> Task:
        task = Task(id=self._next_id(), title=title, description=description, status=status)
        self.tasks.append(task)
        self._save()
        return task

    def update_task(self, task_id: int, *, title: Optional[str] = None, description: Optional[str] = None, status: Optional[str] = None) -> Optional[Task]:
        for task in self.tasks:
            if task.id == task_id:
                if title is not None:
                    task.title = title
                if description is not None:
                    task.description = description
                if status is not None:
                    task.status = status
                self._save()
                return task
        return None

    def remove_task(self, task_id: int) -> bool:
        original_len = len(self.tasks)
        self.tasks = [t for t in self.tasks if t.id != task_id]
        if len(self.tasks) < original_len:
            self._save()
            return True
        return False

    def get_task(self, task_id: int) -> Optional[Task]:
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None

    def list_tasks(self, status: Optional[str] = None) -> List[Task]:
        if status is None:
            return list(self.tasks)
        return [t for t in self.tasks if t.status == status]

    def summary(self) -> Dict[str, int]:
        summary = {"todo": 0, "in_progress": 0, "done": 0}
        for task in self.tasks:
            if task.status in summary:
                summary[task.status] += 1
            else:
                summary[task.status] = summary.get(task.status, 0) + 1
        return summary
