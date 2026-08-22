from datetime import datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import RowMapping
from sqlalchemy.orm import Session

from app.constants import MatchStatusConstants
from app.context import RequestContext
from app.models import Match, MatchTeam
from app.services.query import QueryService
from app.utils.lineup import Lineup, Scores


class MatchTeamsReadListAction:
    """Handle MatchTeams ReadList requests."""

    @staticmethod
    def execute(db: Session, team_id: int | None = None) -> dict:
        """
        Get match teams filtered by team ID.
        Joins with Matches to get match metadata, self-joins to get opposite team data.

        Args:
            db: Database session
            team_id: Filter by teamID (matches where this team participated)

        Returns:
            PHP-compatible response dict with match metadata and opposite team data
        """
        query = db.query(MatchTeam)

        if team_id is not None:
            query = query.filter(MatchTeam.teamID == team_id)
        else:
            query = query.filter(False)

        match_teams = query.order_by(MatchTeam.matchID).all()

        def to_iso(dt):
            if dt is None:
                return None
            if isinstance(dt, str):
                return dt
            return dt.isoformat()

        items = []
        for mt in match_teams:
            # Get the match metadata
            match = db.query(Match).filter(Match.matchID == mt.matchID).first()

            # Get the opposite team (other matchTeamNum for same matchID)
            opposite_num = 2 if mt.matchTeamNum == 1 else 1
            opposite_mt = (
                db.query(MatchTeam)
                .filter(
                    MatchTeam.matchID == mt.matchID,
                    MatchTeam.matchTeamNum == opposite_num,
                )
                .first()
            )

            values = {
                "matchTeamID": mt.matchTeamID,
                "matchID": mt.matchID,
                "matchTeamNum": mt.matchTeamNum,
                "matchStatus": match.matchStatus if match else None,
                "leagueID": match.leagueID if match else None,
                "divisionID": match.divisionID if match else None,
                "season": match.season if match else None,
                "seasonNum": match.seasonNum if match else None,
                "realCompetitionID": match.realCompetitionID if match else None,
                "realCompetitionMatchDay": match.realCompetitionMatchDay
                if match
                else None,
                "realCompetitionMatchDaySort": match.realCompetitionMatchDaySort
                if match
                else None,
                "competitionType": match.competitionType if match else None,
                "competitionMatchDay": match.competitionMatchDay if match else None,
                "competitionLastMatchDay": match.competitionLastMatchDay
                if match
                else None,
                "competitionMatchNumber": match.competitionMatchNumber
                if match
                else None,
                "competitionMatchGroup": match.competitionMatchGroup if match else None,
                "competitionMatchNextGroup": match.competitionMatchNextGroup
                if match
                else None,
                "competitionMatchRound": match.competitionMatchRound if match else None,
                "competitionMatchLastRound": match.competitionMatchLastRound
                if match
                else None,
                "matchGroupWinnerTeamID": match.matchGroupWinnerTeamID
                if match
                else None,
                "userID": mt.userID,
                "teamID": mt.teamID,
                "teamName": mt.teamName,
                "teamScore": mt.teamScore,
                "teamPoints": mt.teamPoints,
                "teamSeeding": mt.teamSeeding,
                "matchDayMapKey": mt.matchDayMapKey,
                "oppositeUserID": opposite_mt.userID if opposite_mt else None,
                "oppositeTeamID": opposite_mt.teamID if opposite_mt else None,
                "oppositeTeamName": opposite_mt.teamName if opposite_mt else None,
                "oppositeTeamScore": opposite_mt.teamScore if opposite_mt else None,
                "oppositeTeamPoints": opposite_mt.teamPoints if opposite_mt else None,
                "oppositeTeamSeeding": opposite_mt.teamSeeding if opposite_mt else None,
                "oppositeMatchDayMapKey": opposite_mt.matchDayMapKey
                if opposite_mt
                else None,
                "lineup": mt.lineup,
                "cntEPLTeam": mt.cntEPLTeam,
                "cntGoalkeeper": mt.cntGoalkeeper,
                "cntDefender": mt.cntDefender,
                "cntMidfielder": mt.cntMidfielder,
                "cntStriker": mt.cntStriker,
                "cntSubstitute": mt.cntSubstitute,
                "cntInactive": mt.cntInactive,
                "createdBy": mt.createdBy,
                "createdIn": to_iso(mt.createdIn),
                "updatedBy": mt.updatedBy,
                "updatedIn": to_iso(mt.updatedIn),
            }
            items.append({"values": values})

        return {
            "table": "MatchTeams",
            "timestamp": RequestContext.get_datetime().strftime("%Y-%m-%d %H:%M:%S"),
            "items": items,
        }


class GetLineupAction:
    """Handle MatchTeams GetLineup requests."""

    @staticmethod
    def _execute(
        db: Session,
        match_team_id: int | None = None,
        team_id: int | None = None,
        competition_type: int | None = None,
        competition_match_day: int | None = None,
        new_lineup: str | None = None,
        save: bool = False,
    ) -> dict | None:
        # filled after reading the row, before load() calls get_key_data

        get_data_cache = KeyDataCache(db)
        lineup = Lineup(db, get_data_cache.get)

        if match_team_id is not None:
            match_team = lineup.read_by_match_team(match_team_id)
        elif (
            team_id is not None
            and competition_type is not None
            and competition_match_day is not None
        ):
            match_team = lineup.read_by_team_id(
                team_id, competition_type, competition_match_day
            )
        else:
            raise ValueError(
                "Either match_team_id or (team_id, competition_type, competition_match_day) must be provided"
            )
        if match_team is None:
            return None

        get_data_cache.init(match_team)

        now = RequestContext.get_datetime()
        match_status = _get_match_status(db, match_team, now)

        if not lineup.load(match_team, match_status, new_lineup=new_lineup):
            return None

        if save:
            lineup.save_lineup()
            db.commit()

        return {
            "table": "MatchTeams",
            "timestamp": RequestContext.get_datetime().strftime("%Y-%m-%d %H:%M:%S"),
            "items": [{"values": m} for m in lineup.get_members()],
        }


class GetLineupByMatchTeamIDAction(GetLineupAction):
    """Handle MatchTeams GetLineupByMatchTeamID requests."""

    @staticmethod
    def execute(db: Session, match_team_id: int) -> dict | None:
        return GetLineupAction._execute(db, match_team_id=match_team_id)


class GetLineupByCompetitionTypeAction:
    """Handle MatchTeams GetLineupByCompetitionType requests."""

    @staticmethod
    def execute(
        db: Session,
        team_id: int,
        competition_type: int,
        competition_match_day: int,
    ) -> dict | None:
        return GetLineupAction._execute(
            db,
            team_id=team_id,
            competition_type=competition_type,
            competition_match_day=competition_match_day,
        )


class SetLineupByCompetitionTypeAction(GetLineupAction):
    """Handle MatchTeams SetLineupByCompetitionType requests."""

    @staticmethod
    def execute(
        db: Session,
        team_id: int,
        competition_type: int,
        competition_match_day: int,
        real_team_id: int,
        real_player_ids: list[int],
        substitute_real_player_ids: list[int],
    ) -> dict | None:
        new_lineup = Lineup.from_ids(
            real_team_id, real_player_ids, substitute_real_player_ids
        )
        return GetLineupAction._execute(
            db,
            team_id=team_id,
            competition_type=competition_type,
            competition_match_day=competition_match_day,
            new_lineup=new_lineup,
            save=True,
        )


class ClearLineupByMatchTeamIDAction:
    """Handle MatchTeams ClearLineupByMatchTeamID requests."""

    @staticmethod
    def execute(db: Session, match_team_id: int, user_id: int) -> dict | None:
        match_team = (
            db.query(MatchTeam).filter(MatchTeam.matchTeamID == match_team_id).first()
        )
        if match_team is None:
            return None
        if match_team.userID != user_id:
            raise PermissionError
        db.execute(
            text(
                "UPDATE `MatchTeams` SET `lineup` = '' WHERE `matchTeamID` = :matchTeamID"
            ),
            {"matchTeamID": match_team_id},
        )
        db.commit()
        return {
            "table": "MatchTeams",
            "timestamp": RequestContext.get_datetime().strftime("%Y-%m-%d %H:%M:%S"),
            "values": {"matchTeamID": match_team_id},
        }


class GetScores:
    @staticmethod
    def _execute(
        db: Session,
        match_ids: list[int] | None = None,
        competition_type: int | None = None,
        competition_match_day: int | None = None,
        league_id: int | None = None,
        division_id: int | None = None,
    ) -> dict | None:

        get_data_cache = KeyDataCache(db)
        scores = Scores(db, get_data_cache.get)

        if match_ids is not None:
            match_teams = scores.read_by_match_ids(match_ids)
        elif (
            competition_type is not None
            and competition_match_day is not None
            and league_id is not None
        ):
            match_teams = scores.read_by_match_day(
                competition_type, competition_match_day, league_id, division_id
            )
        else:
            raise ValueError(
                "Either match_ids or (competition_type, competition_match_day, league_id) must be provided"
            )
        if not match_teams:
            return None

        get_data_cache.init(
            match_teams[0]
        )  # Initialize cache with the first match team

        now = RequestContext.get_datetime()
        match_status = _get_match_status(db, match_teams[0], now)

        if not scores.load(match_teams, match_status):
            return None

        return {
            "table": "MatchTeams",
            "timestamp": RequestContext.get_datetime().strftime("%Y-%m-%d %H:%M:%S"),
            "values": list(scores.get_members()),
        }


class GetScoresByMatchIDsAction:
    """Handle MatchTeams GetScoresByMatchIDs requests."""

    @staticmethod
    def execute(db: Session, match_ids: list[int]) -> dict | None:
        return GetScores._execute(db, match_ids=match_ids)


class GetScoresByMatchDayAction:
    """Handle MatchTeams GetScoresByMatchDay requests."""

    @staticmethod
    def execute(
        db: Session,
        competition_type: int,
        competition_match_day: int,
        league_id: int,
        division_id: int | None = None,
    ) -> dict | None:
        return GetScores._execute(
            db,
            competition_type=competition_type,
            competition_match_day=competition_match_day,
            league_id=league_id,
            division_id=division_id,
        )


def _get_match_status(db: Session, match_team: RowMapping, now: datetime) -> int:
    mds = QueryService.get_current_match_day_status(
        db,
        match_day_map_key=match_team["matchDayMapKey"],
        current_datetime=now,
        include_boundaries=True,
    )
    if mds is None:
        return MatchStatusConstants.NOT_STARTED

    if mds["realCompetitionMatchDaySort"] < match_team["realCompetitionMatchDaySort"]:
        return MatchStatusConstants.NOT_STARTED
    elif mds["realCompetitionMatchDaySort"] > match_team["realCompetitionMatchDaySort"]:
        return MatchStatusConstants.FINISHED
    else:
        start_pre = mds["startPreMatch"]
        start_post = mds["startPostMatch"]
        if start_pre is None or start_pre > now:
            return MatchStatusConstants.NOT_STARTED
        elif start_post is not None and start_post < now:
            return MatchStatusConstants.FINISHED
        else:
            return MatchStatusConstants.PLAYING


class KeyDataCache:
    """Cache for key data used in lineup and scores actions."""

    def __init__(self, db: Session):
        self._cache: dict[str, dict[str, Any]] = {}
        self._db = db
        self._real_competition_id: int | None = None
        self._real_competition_match_day: int | None = None

    @property
    def real_competition_id(self) -> int | None:
        return self._real_competition_id

    @real_competition_id.setter
    def real_competition_id(self, value: int | None):
        self._real_competition_id = value
        self._cache.clear()  # Clear cache when competition ID changes

    @property
    def real_competition_match_day(self) -> int | None:
        return self._real_competition_match_day

    @real_competition_match_day.setter
    def real_competition_match_day(self, value: int | None):
        self._real_competition_match_day = value
        self._cache.clear()  # Clear cache when competition match day changes

    def init(self, match_team: RowMapping):
        """Initialize the cache with match team data."""
        self._real_competition_id = match_team["realCompetitionID"]
        self._real_competition_match_day = match_team["realCompetitionMatchDay"]
        self._cache.clear()  # Clear cache when initializing with new match team

    def get(self, key: str) -> dict[str, Any]:
        if key in self._cache:
            return self._cache[key]
        if (
            self._real_competition_id is None
            or self._real_competition_match_day is None
        ):
            return {}
        standing = QueryService.get_real_standings_by_match_day(
            self._db,
            real_competition_id=self._real_competition_id,
            real_competition_match_day=self._real_competition_match_day,
            real_team_member_key=key,
        )
        self._cache[key] = standing if standing is not None else {}
        return self._cache[key]
