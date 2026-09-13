from collections.abc import Generator
from datetime import datetime
from itertools import pairwise

from sqlmodel import Session, select, text

from app.constants import MatchDayStatusConstants, RealMatchPeriod
from app.models import MatchDaysStatus
from app.services.query import QueryService
from app.utils.dt import (
    add_days,
    add_hours,
    add_minutes,
    next_midnight,
    utc_largest,
    utc_lowest,
)
from app.utils.match_day_map_keys import build_map_days_map_key
from app.utils.tasks import Task


class SaveMDS:
    NUM_MONTHS = 2

    PROCESS_HOURS = 3
    WAIVERS_DAYS = 2
    MINUTES_BEFORE_MATCH = 15
    PRE_MATCH_HOUR = 6
    LATE_PRE_MATCH_HOUR = 12
    LATE_PRE_MATCH_LIMIT = 18
    BASE_MD_HOURS = 5
    BASE_MD_DAYS = 1

    def __init__(self, db: Session, real_competition_id: int | None = None):
        """_summary_

        Args:
            db (Session): _description_
        """
        self._task: Task = Task(name="SaveMDS", status_on_error=Task.ERROR)
        self._db: Session = db
        self._md: list[tuple[int, int]] = []
        self._mmd: dict = {}
        self._rm: dict[tuple[int, int], dict] = {}
        self._mds: list[dict] = []
        self._base_rc_id: int | None = None
        self._extra_rc_id: int | None = None
        self._init_rc(real_competition_id)

    def process(self) -> Task:
        """Create or update all MatchDaysStatus rows for the current season.

        Returns:
            Task: closed task with ``inserted``, ``updated``, and ``errors`` counts.
                  Call ``.to_dict()`` if a serialisable result is needed.
        """
        self._task.init_info("inserted", "updated", "errors")
        if (
            self._valid_rc()
            and self._init_md()
            and self._init_mmd()
            and self._init_rm()
        ):
            for rc_id, div_md, div_cnt, lea_md, lea_cnt in self._combine_md():
                self._process_mds(rc_id, div_md, div_cnt, lea_md, lea_cnt)
            self._fix_prev_mds()
            self._fix_next_mds()
        self._task.close(status=Task.COMPLETED)
        return self._task

    def _combine_md(self) -> Generator[list, None, None]:
        """Generates all possible combinations for MapMatchDays records.

        Yields:
            Generator[list, None, None]: a single combination.
        """
        # Root competition key — no division or league
        yield [self._base_rc_id, None, None, None, None]
        div_mds = list(self._mmd.get("D", {}))
        lea_mds = list(self._mmd.get("L", {}))
        for i, div_md in enumerate(div_mds):
            for div_cnt in self._mmd["D"][div_md]:
                yield [self._base_rc_id, div_md, div_cnt, None, None]
                lea_window = lea_mds[i : i + self.NUM_MONTHS - 1]
                for lea_md in lea_window:
                    for lea_cnt in self._mmd["L"][lea_md]:
                        yield [self._base_rc_id, div_md, div_cnt, lea_md, lea_cnt]

    def _process_mds(
        self,
        rc_id: int,
        div_md: int | None,
        div_cnt: int | None,
        lea_md: int | None,
        lea_cnt: int | None,
    ) -> None:
        """_summary_

        Args:
            rc_id (int): _description_
            div_md (int | None): _description_
            div_cnt (int | None): _description_
            lea_md (int | None): _description_
            lea_cnt (int | None): _description_
        """
        match_day_map_key = build_map_days_map_key(
            rc_id, div_md, div_cnt, lea_md, lea_cnt
        )
        active_keys = self._get_active_keys(div_md, div_cnt, lea_md, lea_cnt)
        self._init_mds(match_day_map_key, active_keys)
        self._add_prev_mds()
        self._add_next_mds()
        self._add_mds_dates()
        self._save_mds()

    def _get_active_keys(
        self,
        div_md: int | None,
        div_cnt: int | None,
        lea_md: int | None,
        lea_cnt: int | None,
    ) -> set[tuple[int, int]]:
        """_summary_

        Args:
            div_md (int | None): _description_
            div_cnt (int | None): _description_
            lea_md (int | None): _description_
            lea_cnt (int | None): _description_

        Returns:
            set[tuple[int, int]]: _description_
        """
        active: set[tuple[int, int]] = set()
        self._add_active_keys(active, div_md, div_cnt, lea_md, lea_cnt)
        return active

    def _add_active_keys(
        self,
        active: set[tuple[int, int]],
        division_md: int | None,
        division_teams: int | None,
        league_md: int | None,
        league_teams: int | None,
    ) -> None:
        """Get the list of match days that are active (present in MapMatchDays)

        Args:
            active (set[tuple[int, int]]): _description_
            division_md (int | None): _description_
            division_teams (int | None): _description_
            league_md (int | None): _description_
            league_teams (int | None): _description_
        """
        if division_md is None:
            # All active keys
            for d_md, d_mds in self._mmd.get("D", {}).items():
                for d_cnt in d_mds:
                    for l_md, lea_mds in self._mmd.get("L", {}).items():
                        for l_cnt in lea_mds:
                            self._add_active_keys(active, d_md, d_cnt, l_md, l_cnt)
        elif league_md is None:
            # Only the division keys
            active.update(self._mmd["D"][division_md][division_teams])
        else:
            # The division and league keys
            self._add_active_keys(active, division_md, division_teams, None, None)
            active.update(self._mmd["L"][league_md][league_teams])

    def _init_mds(
        self, match_day_map_key: str, active_keys: set[tuple[int, int]]
    ) -> None:
        """_summary_

        Args:
            match_day_map_key (str): _description_
            active_keys (set[tuple[int, int]]): _description_
        """
        base_rc = self._base_rc()
        extra_rc = self._extra_rc()
        self._mds = []
        for i, md in enumerate(self._md):
            real_competition_id, real_competition_match_day = md
            rm_entry = self._rm.get(md, {})
            min_date = rm_entry.get("minRealMatchDate")
            max_date = rm_entry.get("maxRealMatchDate")
            rc = base_rc if real_competition_id == self._base_rc_id else extra_rc
            self._mds.append(
                self._read_mds(
                    match_day_map_key,
                    rc["realCompetitionID"],
                    real_competition_match_day,
                )
                | {
                    "baseRealCompetitionID": self._base_rc_id,
                    "extraRealCompetitionID": self._extra_rc_id,
                    "matchDayMapKey": match_day_map_key,
                    "realCompetitionID": rc["realCompetitionID"],
                    "realCompetitionSYMID": rc["realCompetitionSYMID"],
                    "realCompetitionSeasonId": rc["realCompetitionSeasonId"],
                    "realCompetitionMatchDay": real_competition_match_day,
                    "realCompetitionMatchDaySort": i + 1,
                    "active": int(md in active_keys),
                    "overlapped": 0,
                    "minRealMatchDate": min_date,
                    "maxRealMatchDate": max_date,
                }
            )

    def _read_mds(
        self,
        match_day_map_key: str,
        real_competition_id: int,
        real_competition_match_day: int,
    ) -> dict:
        """Look up an existing MatchDaysStatus row by its natural key.

        Returns:
            A dict with at least ``matchDayStatusID`` and ``locked``.
            For locked rows all date fields are included so they can be
            preserved through the ``_init_mds`` merge.
            Returns ``{"locked": 0}`` when no row exists yet.
        """
        row = self._db.exec(
            select(
                MatchDaysStatus.matchDayStatusID,
                MatchDaysStatus.locked,
                MatchDaysStatus.startWaivers,
                MatchDaysStatus.finishWaivers,
                MatchDaysStatus.startWaiversSettle,
                MatchDaysStatus.finishWaiversSettle,
                MatchDaysStatus.startOpenWaivers,
                MatchDaysStatus.finishOpenWaivers,
                MatchDaysStatus.startOpenWaiversSettle,
                MatchDaysStatus.finishOpenWaiversSettle,
                MatchDaysStatus.startPreMatch,
                MatchDaysStatus.finishPreMatch,
                MatchDaysStatus.startMatch,
                MatchDaysStatus.finishMatch,
                MatchDaysStatus.startPostMatch,
                MatchDaysStatus.finishPostMatch,
            ).where(
                MatchDaysStatus.matchDayMapKey == match_day_map_key,
                MatchDaysStatus.realCompetitionID == real_competition_id,
                MatchDaysStatus.realCompetitionMatchDay == real_competition_match_day,
            )
        ).first()
        if not row:
            return {"locked": 0}
        mds = {"matchDayStatusID": row.matchDayStatusID, "locked": row.locked}
        if mds["locked"]:
            mds["startWaivers"] = row.startWaivers
            mds["finishWaivers"] = row.finishWaivers
            mds["startWaiversSettle"] = row.startWaiversSettle
            mds["finishWaiversSettle"] = row.finishWaiversSettle
            mds["startOpenWaivers"] = row.startOpenWaivers
            mds["finishOpenWaivers"] = row.finishOpenWaivers
            mds["startOpenWaiversSettle"] = row.startOpenWaiversSettle
            mds["finishOpenWaiversSettle"] = row.finishOpenWaiversSettle
            mds["startPreMatch"] = row.startPreMatch
            mds["finishPreMatch"] = row.finishPreMatch
            mds["startMatch"] = row.startMatch
            mds["finishMatch"] = row.finishMatch
            mds["startPostMatch"] = row.startPostMatch
            mds["finishPostMatch"] = row.finishPostMatch
        return mds

    def _add_prev_mds(self) -> None:
        """_summary_"""
        prev_mds: dict | None = None
        for mds in self._mds:
            mds["prevActiveRealCompetitionID"] = (
                prev_mds and prev_mds["realCompetitionID"]
            )
            mds["prevActiveRealCompetitionSYMID"] = (
                prev_mds and prev_mds["realCompetitionSYMID"]
            )
            mds["prevActiveRealCompetitionSeasonId"] = (
                prev_mds and prev_mds["realCompetitionSeasonId"]
            )
            mds["prevActiveRealCompetitionMatchDay"] = (
                prev_mds and prev_mds["realCompetitionMatchDay"]
            )
            if mds["active"]:
                prev_mds = mds

    def _add_next_mds(self) -> None:
        """_summary_"""
        next_mds: dict | None = None
        for mds in reversed(self._mds):
            mds["nextActiveRealCompetitionID"] = (
                next_mds and next_mds["realCompetitionID"]
            )
            mds["nextActiveRealCompetitionSYMID"] = (
                next_mds and next_mds["realCompetitionSYMID"]
            )
            mds["nextActiveRealCompetitionSeasonId"] = (
                next_mds and next_mds["realCompetitionSeasonId"]
            )
            mds["nextActiveRealCompetitionMatchDay"] = (
                next_mds and next_mds["realCompetitionMatchDay"]
            )
            if mds["active"]:
                next_mds = mds

    def _add_mds_dates(self) -> None:
        """_summary_"""
        statuses = MatchDayStatusConstants.valid_values()
        prev_active = None
        lowest_date = utc_lowest()
        for i, mds in enumerate(self._mds):
            mds["startMatchDay"] = self._start_match_day(i)
            mds["finishMatchDay"] = self._finish_match_day(i)
            mds["finishBaseMatchDay"] = self._finish_base_match_day(i)
            if mds["active"]:
                if not mds["locked"]:
                    self._calc_mds_dates(i, prev_active, lowest_date)
                for prev, curr in pairwise(statuses):
                    mds["start" + curr] = mds["finish" + prev]
                self._check_overlapped(i, prev_active, statuses)
                prev_active = i
            else:
                for status in statuses:
                    mds["start" + status] = None
                    mds["finish" + status] = None
        if prev_active is not None:
            # This has to run even when the record is locked
            self._mds[prev_active]["finishPostMatch"] = utc_largest()

    def _calc_mds_dates(
        self, i: int, prev_active: int | None, lowest_date: datetime
    ) -> None:
        """Calculates the status dates for the match day.

        Args:
            i (int): the current (active) match day
            prev_active (int | None): previous active match day
            lowest_date (datetime): for the first active match day
        """
        if prev_active is None:
            # The first one
            self._mds[i]["startWaivers"] = lowest_date
            self._mds[i]["finishWaivers"] = lowest_date
            self._mds[i]["finishWaiversSettle"] = lowest_date
        else:
            # All the remaining cases
            self._mds[i]["startWaivers"] = self._mds[prev_active]["finishPostMatch"]
            self._mds[i]["finishWaivers"] = self._finish_waivers(i)
            self._mds[i]["finishWaiversSettle"] = self._finish_waivers_settle(i)
        self._mds[i]["finishOpenWaivers"] = self._finish_open_waivers(i)
        self._mds[i]["finishOpenWaiversSettle"] = self._mds[i]["finishOpenWaivers"]
        self._mds[i]["finishPreMatch"] = self._mds[i]["startMatchDay"]
        self._mds[i]["finishMatch"] = self._mds[i]["finishMatchDay"]
        self._mds[i]["finishPostMatch"] = self._finish_post_match(i)

    def _check_overlapped(
        self, i: int, prev_active: int | None, statuses: tuple[str, ...]
    ) -> None:
        """_summary_

        Args:
            i (int): _description_
            prev_active (int | None): _description_
            statuses (tuple[str, ...]): _description_
        """
        self._mds[i]["overlapped"] = 0
        for s, status in enumerate(statuses):
            if self._mds[i]["start" + status] > self._mds[i]["finish" + status]:
                self._mds[i]["overlapped"] = 1
                if s == 0 and prev_active is not None:
                    self._mds[prev_active]["overlapped"] = 1

    def _start_match_day(self, i: int) -> datetime:
        """_summary_

        Args:
            i (int): _description_

        Returns:
            datetime: _description_
        """
        return add_minutes(self._mds[i]["minRealMatchDate"], -self.MINUTES_BEFORE_MATCH)

    def _finish_match_day(self, i: int) -> datetime:
        """_summary_

        Args:
            i (int): _description_

        Returns:
            datetime: _description_
        """
        return next_midnight(self._mds[i]["maxRealMatchDate"])

    def _finish_base_match_day(self, i: int) -> datetime:
        """_summary_

        Args:
            i (int): _description_

        Returns:
            datetime: _description_
        """
        if i == 0:
            return utc_lowest()
        return add_hours(
            add_days(self._mds[i - 1]["finishMatchDay"], self.BASE_MD_DAYS),
            self.BASE_MD_HOURS,
        )

    def _finish_waivers_settle(self, i: int) -> datetime:
        """_summary_

        Args:
            i (int): _description_

        Returns:
            datetime: _description_
        """
        # startWaiversSettle = finishWaivers (set after add_dates loop body),
        # so compute directly from finishWaivers to avoid the ordering dependency.
        return add_hours(self._mds[i]["finishWaivers"], self.PROCESS_HOURS)

    def _finish_waivers(self, i: int) -> datetime:
        """_summary_

        Args:
            i (int): _description_

        Returns:
            datetime: _description_
        """
        return add_days(self._mds[i]["startWaivers"], self.WAIVERS_DAYS).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

    def _finish_open_waivers(self, i: int) -> datetime:
        """_summary_

        Args:
            i (int): _description_

        Returns:
            datetime: _description_
        """
        hour = (
            self.LATE_PRE_MATCH_HOUR
            if self._mds[i]["startMatchDay"].hour > self.LATE_PRE_MATCH_LIMIT
            else self.PRE_MATCH_HOUR
        )
        return self._mds[i]["startMatchDay"].replace(
            hour=hour, minute=0, second=0, microsecond=0
        )

    def _finish_post_match(self, i: int) -> datetime:
        """_summary_

        Args:
            i (int): _description_

        Returns:
            datetime: _description_
        """
        return add_hours(self._mds[i]["finishMatch"], self.PROCESS_HOURS)

    def _save_mds(self) -> None:
        """Insert or update MatchDaysStatus records.

        ``matchDayStatusID`` and ``locked`` are already present in each
        mds_data entry (populated by ``_init_mds`` via ``_read_mds``).
        New records (no ID) are inserted; existing ones go through
        pre-update logic before their fields are written.
        """
        for mds_data in self._mds:
            try:
                match_day_status_id = mds_data.get("matchDayStatusID")
                locked = mds_data.get("locked", 0)  # noqa: F841  (reserved for pre-update logic)
                if match_day_status_id is None:
                    self._db.add(MatchDaysStatus(**mds_data))
                    self._task.inc("inserted")
                else:
                    existing = self._db.get(MatchDaysStatus, match_day_status_id)
                    # --- pre-update logic ---

                    # --- end pre-update logic ---
                    for key, value in mds_data.items():
                        setattr(existing, key, value)
                    self._task.inc("updated")
                self._db.flush()
            except Exception as e:  # noqa: BLE001
                self._db.rollback()
                self._task.add_error(str(e))
                self._task.inc("errors")
                continue
        self._db.commit()

    def _fix_prev_mds(self) -> None:
        """Update prevActiveMatchDayStatusID."""
        sql = text("""
                   UPDATE `MatchDaysStatus` `m1`
                      INNER JOIN `MatchDaysStatus` `m2`
                         ON `m1`.`matchDayMapKey` = `m2`.`matchDayMapKey` AND
                            `m1`.`prevActiveRealCompetitionID` = `m2`.`realCompetitionID` AND
                            `m1`.`prevActiveRealCompetitionMatchDay` = `m2`.`realCompetitionMatchDay`
                      SET `m1`.`prevActiveMatchDayStatusID` = `m2`.`matchDayStatusID`
                   """)
        self._db.execute(sql)  # type: ignore[call-overload]  # raw UPDATE via text()
        self._db.commit()

    def _fix_next_mds(self) -> None:
        """Update nextActiveMatchDayStatusID."""
        sql = text("""
                   UPDATE `MatchDaysStatus` `m1`
                      INNER JOIN `MatchDaysStatus` `m2`
                         ON `m1`.`matchDayMapKey` = `m2`.`matchDayMapKey` AND
                            `m1`.`nextActiveRealCompetitionID` = `m2`.`realCompetitionID` AND
                            `m1`.`nextActiveRealCompetitionMatchDay` = `m2`.`realCompetitionMatchDay`
                      SET `m1`.`nextActiveMatchDayStatusID` = `m2`.`matchDayStatusID`
                   """)
        self._db.execute(sql)  # type: ignore[call-overload]  # raw UPDATE via text()
        self._db.commit()

    def _base_rc(self) -> dict:
        """Get the base RealCompetition data for the current season.
           The record is cached in QueryService.

        Returns:
            dict: The base RealCompetition data, or an empty dict if no base competition exists.
        """
        rc = QueryService.get_competition(self._db, self._base_rc_id)
        return rc if rc is not None else {}

    def _extra_rc(self) -> dict:
        """Get the extra RealCompetition data for the current season.
           The record is cached in QueryService.

        Returns:
            dict: The extra RealCompetition data, or an empty dict if no extra competition exists.
        """
        rc = QueryService.get_competition(self._db, self._extra_rc_id)
        return rc if rc is not None else {}

    def _init_rc(self, real_competition_id: int | None = None) -> None:
        if real_competition_id is None:
            rc = QueryService.get_current_base_competition(self._db)
        else:
            rc = QueryService.get_competition(self._db, real_competition_id)
        if isinstance(rc, dict):
            self._base_rc_id = rc.get("baseRealCompetitionID")
            self._extra_rc_id = rc.get("extraRealCompetitionID")

    def _valid_rc(self) -> bool:
        return isinstance(self._base_rc_id, int) and isinstance(self._extra_rc_id, int)

    def _init_md(self) -> bool:
        """Initilizes the list of match days.

        Returns:
            bool: True on success
        """
        base_rc = self._base_rc()
        extra_rc = self._extra_rc()
        start_md = base_rc["realCompetitionFirstMatchDay"]
        end_md = base_rc["realCompetitionLastMatchDay"]
        if (
            base_rc["useExtraRealCompetition"]
            and base_rc["realCompetitionExtraMatchDay"]
        ):
            extra_md = base_rc["realCompetitionExtraMatchDay"]
            end_md += 1
        else:
            extra_md = None
        self._md = []
        for i in range(start_md, end_md + 1):
            self._md.append((base_rc["realCompetitionID"], i))
            if extra_md == i:
                self._md.append(
                    (
                        extra_rc["realCompetitionID"],
                        extra_rc["realCompetitionFirstMatchDay"],
                    )
                )
        return len(self._md) > 0

    def _init_mmd(self) -> bool:
        """Read MatchDaysMap rows for the current base competition.

        Returns a nested dict structured as::

            {
                'D': {firstRealCompetitionMatchDay: {maxNumTeams: [(rcID, rcMatchDay), ...]}},
                'L': {firstRealCompetitionMatchDay: {maxNumTeams: [(rcID, rcMatchDay), ...]}},
            }

        'D' entries are division schedule slots (competitionType != 3);
        'L' entries are league schedule slots (competitionType == 3).
        Rows are ordered by firstRealCompetitionMatchDay, competitionType,
        maxNumTeams, and matchDay.
        """
        sql = text("""
                   SELECT `firstRealCompetitionMatchDay`,
                          `competitionType`,
                          `maxNumTeams`,
                          `matchDay`,
                          `realCompetitionID`,
                          `realCompetitionMatchDay`
                      FROM `MatchDaysMap`
                      WHERE `baseRealCompetitionID` = :baseRealCompetitionID
                      ORDER BY `firstRealCompetitionMatchDay`,
                               `competitionType`,
                               `maxNumTeams`,
                               `matchDay`
                   """)
        rows = (
            self._db.execute(  # type: ignore[call-overload]  # raw text() query needs .mappings()
                sql,
                {"baseRealCompetitionID": self._base_rc_id},
            )
            .mappings()
            .all()
        )
        self._mmd = {}
        for row in rows:
            d_or_l = "D" if row["competitionType"] != 3 else "L"
            first_md = row["firstRealCompetitionMatchDay"]
            max_num_teams = row["maxNumTeams"]
            value = (row["realCompetitionID"], row["realCompetitionMatchDay"])
            if d_or_l not in self._mmd:
                self._mmd[d_or_l] = {}
            if first_md not in self._mmd[d_or_l]:
                self._mmd[d_or_l][first_md] = {}
            if max_num_teams not in self._mmd[d_or_l][first_md]:
                self._mmd[d_or_l][first_md][max_num_teams] = []
            self._mmd[d_or_l][first_md][max_num_teams].append(value)
        return len(self._mmd) > 0

    def _init_rm(self) -> bool:
        """Load RealMatches date ranges, keyed by (realCompetitionID, realCompetitionMatchDay).

        Returns a dict mapping ``(rcID, matchDay)`` to a dict with
        ``minRealMatchDate`` and ``maxRealMatchDate`` for that match day.
        """
        ids = [self._base_rc_id] + ([self._extra_rc_id] if self._extra_rc_id else [])
        sql = text("""
                   SELECT  `realCompetitionID`,
                           `realCompetitionMatchDay`,
                           MIN(`realMatchDate`) AS `minRealMatchDate`,
                           MAX(`realMatchDate`) AS `maxRealMatchDate`
                      FROM `RealMatches`
                      WHERE `realCompetitionID` IN :ids
                        AND `realMatchPeriod` <> :realMatchPeriod
                        AND `realMatchIgnore` <> 1
                      GROUP BY `realCompetitionID`,
                               `realCompetitionMatchDay`
                      ORDER BY `realCompetitionID`,
                               `realCompetitionMatchDay`
                   """)
        rows = (
            self._db.execute(
                sql, {"ids": ids, "realMatchPeriod": RealMatchPeriod.POSTPONED}
            )
            .mappings()
            .all()
        )  # type: ignore[call-overload]  # aggregate text() query
        self._rm = {}
        for row in rows:
            key = (row["realCompetitionID"], row["realCompetitionMatchDay"])
            self._rm[key] = {
                "minRealMatchDate": row["minRealMatchDate"],
                "maxRealMatchDate": row["maxRealMatchDate"],
            }
        return len(self._rm) > 0
