"""Task scheduler for periodic OAS operations."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Callable


class TaskStatus(Enum):
    """Status of a scheduled task."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Task:
    """A scheduled task."""

    task_id: str
    name: str
    fn: Callable[[], None]
    status: TaskStatus = TaskStatus.PENDING
    last_run: datetime | None = None
    next_run: datetime | None = None
    error: str | None = None
    metadata: dict = field(default_factory=dict)


class Scheduler:
    """Simple task scheduler for OAS operations."""

    def __init__(self):
        self.tasks: dict[str, Task] = {}

    def register(self, task: Task) -> None:
        """Register a task."""
        self.tasks[task.task_id] = task

    def run_task(self, task_id: str) -> None:
        """Run a task by ID."""
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        task.status = TaskStatus.RUNNING
        task.last_run = datetime.now(timezone.utc)

        try:
            task.fn()
            task.status = TaskStatus.COMPLETED
            task.error = None
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)

    def run_all(self) -> None:
        """Run all pending tasks."""
        for task_id in list(self.tasks.keys()):
            if self.tasks[task_id].status == TaskStatus.PENDING:
                self.run_task(task_id)

    def get_status(self, task_id: str) -> TaskStatus | None:
        """Get task status."""
        task = self.tasks.get(task_id)
        return task.status if task else None
