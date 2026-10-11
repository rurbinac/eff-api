from datetime import datetime

from sqlalchemy.orm import Session

from app.utils.processes import Process, Task
from app.utils.readers import KeysReader
from app.utils.rtm_changes import SettleWaivers as SettleWaiversBase


class SettleWaivers(SettleWaiversBase):
    def __init__(self, db: Session, reader: KeysReader, process: Process | None = None):
        super().__init__(db, reader)
        self._process = process
        self._execute_task: Task | None = None

    def execute(self, competition_id: int | None = None, now: datetime | None = None) -> None:
        self._execute_task = (
            self._process.create_task("execute", status=Task.RUNNING, status_on_error=Task.ERROR)
            if self._process is not None
            else None
        )
        if self._execute_task is not None:
            self._execute_task.init_info("divisions", default=0)
            self._execute_task.assign("competition_id", competition_id)
        super().execute(competition_id, now)
        if self._execute_task is not None:
            self._execute_task.close(status=Task.COMPLETED if not self._execute_task.errors else Task.ERROR)
        if self._process is not None:
            self._process.finish()

    def _process_division(self, teams) -> None:
        task = (
            Task(process=self._process, name="_process_division", status=Task.RUNNING, status_on_error=Task.ERROR)
            if self._process is not None
            else None
        )
        if task is not None:
            task.assign("division_id", teams[0].divisionID)
            task.assign("teams", len(teams))
        super()._process_division(teams)
        if task is not None:
            task.close(status=Task.COMPLETED if not task.errors else Task.ERROR)
        if self._execute_task is not None and task is not None:
            self._execute_task.inc("divisions")
            self._execute_task.add_subtask(task)
