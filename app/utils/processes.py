from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.utils.dt import utc_now


class Process:

    @staticmethod
    def init_feeds_process(db: Session, feed_type: str, feed_name: str) -> Process:
        return Process(db, f"Feed:{feed_type}", feed_name)

    @staticmethod
    def init_sync_real_process(db: Session, sync_name: str, prevProcess: Process | None = None) -> Process:
        return Process(db, "SyncReal", sync_name, prevProcess.process_id if prevProcess else None)

    @staticmethod
    def init_sync_fantasy_process(db: Session, sync_name: str, prevProcess: Process | None = None) -> Process:
        return Process(db, "SyncFantasy", sync_name, prevProcess.process_id if prevProcess else None)

    @staticmethod
    def init_save_mds_process(db: Session, sync_name: str, prevProcess: Process | None = None) -> Process:
        return Process(db, "SaveMDS", sync_name, prevProcess.process_id if prevProcess else None)

    @staticmethod
    def init_settle_matches_process(db: Session, rc_id: int | None = None, prevProcess: Process | None = None) -> Process:
        return Process(db, "SettleMatches", str(rc_id) if rc_id is not None else "auto", prevProcess.process_id if prevProcess else None)

    @staticmethod
    def init_settle_waivers_process(db: Session, rc_id: int | None = None, prevProcess: Process | None = None) -> Process:
        return Process(db, "SettleWaivers", str(rc_id) if rc_id is not None else "auto", prevProcess.process_id if prevProcess else None)

    def __init__(self, db: Session, process_type: str, process_name: str, prev_process_id: int | None = None):
        from app.models import Process as ProcessModel
        self._db: Session = db
        self._process_id: int | None = None
        self._prev_process_id: int | None = prev_process_id
        self._process_type: str = process_type
        self._process_name: str = process_name
        self._startDate: datetime | None = None
        self._finishDate: datetime | None = None
        self._versions: int | None = None
        self._sha256: bytes | None = None
        self._tasks: list[Task | dict] | None = None
        self._is_new: bool = False

        row = (
            self._db.query(ProcessModel)
            .filter(ProcessModel.processType == process_type)
            .filter(ProcessModel.processName == process_name)
            .first()
        )
        if row is None:
            self._startDate = utc_now(microsecond=True)
            self._versions = 1
            self._tasks = []
            new_row = ProcessModel(
                processType=self._process_type,
                processName=self._process_name,
                startDate=self._startDate,
            )
            self._db.add(new_row)
            self._db.flush()
            self._process_id = new_row.processID
            self._is_new = True
        else:
            self._process_id = row.processID
            self._prev_process_id = row.prevProcessID
            self._startDate = row.startDate
            self._finishDate = row.finishDate
            self._versions = row.versions
            self._sha256 = row.sha256
            self._tasks = list(row.tasks.values()) if row.tasks else []

    def reset(self, sha256: bytes | None = None) -> bool:
        if self._process_id is not None:
            self._prev_process_id = self._process_id
            self._startDate = utc_now(microsecond=True)
            self._finishDate = None
            self._versions = (self._versions or 0) + 1
            self._sha256 = sha256
            self._tasks = []
            self._is_new = True
            self.save()
            return True
        return False

    @property
    def is_new(self) -> bool:
        return self._is_new

    @property
    def process_id(self) -> int | None:
        return self._process_id

    @property
    def prev_process_id(self) -> int | None:
        return self._prev_process_id

    @property
    def process_type(self) -> str | None:
        return self._process_type

    @property
    def process_name(self) -> str | None:
        return self._process_name

    @property
    def tasks(self) -> list[dict | Task]:
        return self._tasks

    @property
    def startDate(self) -> datetime | None:
        return self._startDate

    @property
    def finishDate(self) -> datetime | None:
        return self._finishDate

    @property
    def sha256(self) -> bytes | None:
        return self._sha256

    @sha256.setter
    def sha256(self, value: bytes | None) -> None:
        self._sha256 = value

    @property
    def versions(self) -> int:
        return self._versions

    @property
    def duration(self) -> float | None:
        if self._startDate is None:
            return None
        return _duration(self._startDate, self._finishDate)

    def create_task(
        self,
        name: str,
        status: str | None = None,
        status_on_error: str | None = None,
    ) -> Task:
        task = Task(process=self, name=name, status=status, status_on_error=status_on_error)
        self._tasks.append(task)
        return task

    def finish(self) -> None:
        if self._is_new and self._startDate is not None and self._finishDate is None:
            self._finishDate = utc_now(microsecond=True)
            self.save()

    def save(self) -> bool:
        from app.models import Process as ProcessModel
        if not self._is_new:
            return False
        self._db.merge(ProcessModel(
            processID=self._process_id,
            prevProcessID=self._prev_process_id,
            processType=self._process_type,
            processName=self._process_name,
            startDate=self._startDate or utc_now(microsecond=True),
            finishDate=self._finishDate,
            duration=self.duration,
            versions=self._versions,
            sha256=self._sha256,
            tasks={t.name: t.to_dict() for t in self._tasks} if self._tasks else None,
        ))
        self._db.flush()
        return True


@dataclass
class Task:
    # These are the possible status values for a task. They are defined as class variables
    #    to provide a clear and consistent way to represent the state of a task.
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"

    name: str
    process: Process | None = field(default=None, repr=False)
    start: datetime = field(default_factory=lambda: utc_now(microsecond=True))
    end: datetime | None = None
    status: str | None = None
    status_on_error: str | None = None
    info: dict[str, str | int | None] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    tasks: list[Task] = field(default_factory=list)
    _stopped_time: datetime | None = field(default=None, init=False, repr=False)
    _paused_s: float = field(default=0.0, init=False, repr=False)

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
        self._paused_s += (
            utc_now(microsecond=True) - self._stopped_time
        ) / timedelta(seconds=1)
        self._stopped_time = None
        return True

    @property
    def duration(self) -> float:
        """Get the elapsed duration of the task in microseconds.

        For a closed task returns the total active time (end − start − paused).
        For an open task returns the time elapsed so far, excluding any paused interval.

        Returns:
            float: Elapsed microseconds, excluding paused time.
        """
        if self.is_closed:
            return _duration(self.start, self.end, self._paused_s)
        now = utc_now(microsecond=True)
        paused_s = self._paused_s
        if self.is_paused:
            paused_s += (now - self._stopped_time) / timedelta(seconds=1)
        return _duration(self.start, now, paused_s)

    def add_subtask(self, subtask: Task) -> None:
        """Add a subtask to the task.

        Args:
            subtask (Task): the subtask to add
        """
        if subtask is self:
            raise ValueError("Cannot add a task as a subtask of itself.")
        if self.contains_task(subtask):
            raise ValueError(
                "Cannot add a subtask that is already in the task's subtree."
            )
        if subtask.contains_task(self):
            raise ValueError(
                "Cannot add a subtask that contains this task in its subtree."
            )
        subtask.process = self.process
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

    def init_info(self, *names: str, default: str | int | None = None) -> None:
        """Initialize info keys with a default value.

        Args:
            *names (str): the names of the info keys to initialize.
            default (str | int | None, optional): value to assign to each key. Defaults to None.
        """
        for name in names:
            self.info[name] = default

    def assign(self, name: str, value: str | int | None) -> str | int | None:
        """Assign a value to an info key.

        Args:
            name (str): the name of the info key to assign
            value (str | int | None): the value to assign to the info key
        """
        self.info[name] = value
        return value

    def inc(self, name: str, amount: int = 1) -> int:
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
            raise TypeError(
                f"Cannot increment non-integer value for '{name}': {current!r}"
            )
        return self.info[name]

    def remove(self, name: str) -> str | int | None:
        """Remove an info key from the task's info dictionary.

        Args:
            name (str): the name of the info key to remove.

        Returns:
            str | int | None: the value that was removed, or None if the key did not exist.
        """
        if name in self.info:
            value = self.info[name]
            del self.info[name]
            return value
        return None

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
            if self.process is not None:
                self.process.save()
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


def _duration(start: datetime, end: datetime | None, paused_s: float  = 0) -> float:
    if end is None:
        end = utc_now(microsecond=True)
    return (end - start) / timedelta(seconds=1) - paused_s

