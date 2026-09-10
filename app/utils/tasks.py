from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from app.utils.dt import utc_now


@dataclass
class Task:

    # These are the possible status values for a task. They are defined as class variables
    #    to provide a clear and consistent way to represent the state of a task.
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"

    name: str
    start: datetime = field(default_factory=lambda: utc_now(microsecond=True))
    end: datetime | None = None
    status: str | None = None
    status_on_error: str | None = None
    info: dict[str, str | int | None] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    tasks: list[Task] = field(default_factory=list)
    _stopped_time: datetime | None = field(default=None, init=False, repr=False)
    _paused_secs: float = field(default=0.0, init=False, repr=False)

    @property
    def start_time(self) -> datetime:
        """Get the start time of the task.

        Returns:
            datetime: The start time of the task.
        """
        return self.start.replace(microsecond=0)

    @property
    def end_time(self) -> datetime | None:
        """Get the end time of the task.

        Returns:
            datetime | None: The end time of the task, or None if the task is not closed.
        """
        return self.end.replace(microsecond=0) if self.end is not None else None

    @property
    def is_closed(self) -> bool:
        """Check if the task is closed.

        Returns:
            bool: True if the task is closed, False otherwise.
        """
        return self.end is not None

    @property
    def is_paused(self) -> bool:
        """Check if the task is currently paused.

        Returns:
            bool: True if the task is paused, False otherwise.
        """
        return self._stopped_time is not None

    def pause(self) -> bool:
        """Pause the task, stopping the duration clock.

        Returns:
            bool: True if the task was paused, False if already closed or paused.
        """
        if self.is_closed or self.is_paused:
            return False
        self._stopped_time = utc_now(microsecond=True)
        return True

    def restart(self) -> bool:
        """Resume a paused task, resuming the duration clock.

        Returns:
            bool: True if the task was resumed, False if already closed or not paused.
        """
        if self.is_closed or not self.is_paused:
            return False
        self._paused_secs += (utc_now(microsecond=True) - self._stopped_time).total_seconds()
        self._stopped_time = None
        return True

    @property
    def duration(self) -> float:
        """Get the duration of the task.

        Returns:
            float | None: The duration of the task in seconds, or None if the task is not closed.
        """
        if self.is_closed:
            return (self.end - self.start).total_seconds() - self._paused_secs
        now = utc_now(microsecond=True)
        paused_secs = self._paused_secs
        if self.is_paused:
            paused_secs += (now - self._stopped_time).total_seconds()
        return (now - self.start).total_seconds() - paused_secs

    def add_subtask(self, subtask: Task) -> None:
        """Add a subtask to the task.

        Args:
            subtask (Task): the subtask to add
        """
        if subtask is self:
            raise ValueError("Cannot add a task as a subtask of itself.")
        if self.contains_task(subtask):
            raise ValueError("Cannot add a subtask that is already in the task's subtree.")
        if subtask.contains_task(self):
            raise ValueError("Cannot add a subtask that contains this task in its subtree.")
        self.tasks.append(subtask)

    def contains_task(self, task: Task) -> bool:
        """Check if this task contains the given task in its subtree.

        Args:
            task (Task): the task to check for

        Returns:
            bool: True if this task contains the given task
        """
        stack = [self]
        while stack:
            current = stack.pop()
            if current is task:
                return True
            stack.extend(current.tasks)
        return False



    def init_info(self, *names: str) -> None:
        """Initialize info keys with None values.

        Args:
            *names (str): the names of the info keys to initialize
        """
        for name in names:
            self.info[name] = None

    def assign(self, name: str, value: str | int | None) -> None:
        """Assign a value to an info key.

        Args:
            name (str): the name of the info key to assign
            value (str | int | None): the value to assign to the info key
        """
        self.info[name] = value

    def inc(self, name: str, amount: int = 1) -> None:
        """Increment the value of an info key in the task's info dictionary.

        Args:
            name (str): the name of the info key to increment
            amount (int, optional): the amount to increment the info key by. Defaults to 1.
        """
        current = self.info.get(name)
        if isinstance(current, int):
            self.info[name] = current + amount
        elif current is None or name not in self.info:
            self.info[name] = amount
        else:
            raise TypeError(f"Cannot increment non-integer value for '{name}': {current!r}")

    def remove(self, name: str) -> None:
        """Remove an info key from the task's info dictionary.

        Args:
            name (str): the name of the info key to remove from the task's info dictionary
        """
        if name in self.info:
            del self.info[name]

    def close(self, status: str | None = None) -> dict:
        """Close the task by setting its end time and optionally updating its status.

        Args:
            status (str | None, optional): the status message for the task. Defaults to None.

        Returns:
            dict: the dictionary representation of the Task object, including its attributes and any nested subtasks.
        """
        if not self.is_closed:
            self.restart()  # Ensure any paused time is accounted for before closing
            self.end = utc_now(microsecond=True)
            if status is not None:
                self.status = status
            if self.status_on_error is not None and self.errors:
                self.status = self.status_on_error
        return self.to_dict()

    def add_error(self, error: str) -> None:
        """Add an error message to the task's error list.

        Args:
            error (str): the error message to be added to the task's error list
        """
        self.errors.append(error)

    def to_dict(self) -> dict:
        """Transform the Task object into a dictionary representation.

        Returns:
            dict: the dictionary representation of the Task object, including its attributes and any nested subtasks.
        """
        data = {
            "name": self.name,
            "start": self.start_time.isoformat(),
            "end": self.end_time.isoformat() if self.end_time else None,
            "duration": self.duration,
        }
        if self.status is not None:
            data["status"] = self.status
        if self.errors:
            data["errors"] = self.errors
        if self.info:
            data["info"] = self.info
        if self.tasks:
            data["tasks"] = [task.to_dict() for task in self.tasks]
        return data
