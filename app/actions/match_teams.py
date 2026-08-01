from datetime import datetime
from typing import Any

from sqlalchemy.engine import RowMapping
from sqlalchemy.orm import Session

from app.constants import MatchStatusConstants
from app.context import RequestContext
from app.models import Match, MatchTeam
from app.services.query import QueryService
from app.utils.lineup import Lineup



class MatchTeamsReadListAction:
    """Handle MatchTeams ReadList requests."""

    @staticmethod
    def execute(db: Session, team_id: int | None = None) -> list[dict]:
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


class GetLineupByMatchTeamIDAction:
    """Handle MatchTeams GetLineupByMatchTeamID requests."""

    @staticmethod
    def execute(db: Session, match_team_id: int) -> dict | None:
        # filled after reading the row, before load() calls get_key_data
        real_competition_id: int | None = None
        real_match_day: int | None = None
        cache: dict[str, dict[str, Any]] = {}

        def get_key_data(key: str) -> dict[str, Any]:
            if key in cache:
                return cache[key]
            if real_competition_id is None or real_match_day is None:
                return {}
            standing = QueryService.get_real_standings_by_match_day(
                db,
                real_competition_id=real_competition_id,
                real_competition_match_day=real_match_day,
                real_team_member_key=key,
            )
            cache[key] = standing if standing is not None else {}
            return cache[key]

        def get_match_status(match_team: RowMapping, now: datetime) -> str:
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

        lineup = Lineup(db, get_key_data)
        match_team = lineup.read_by_match_team(match_team_id)
        if match_team is None:
            return None

        real_competition_id = match_team["realCompetitionID"]
        real_match_day = match_team["realCompetitionMatchDay"]

        now = RequestContext.get_datetime()
        match_status = get_match_status(match_team, now)

        if not lineup.load(match_team, match_status):
            return None

        return {
            "table": "MatchTeams",
            "timestamp": RequestContext.get_datetime().strftime("%Y-%m-%d %H:%M:%S"),
            "values": {
                "matchTeamID": lineup.match_team_id,
                "matchID": lineup.match_id,
                "teamID": lineup.team_id,
                "userID": lineup.user_id,
                "matchStatus": lineup.match_status,
                "competitionType": lineup.competition_type,
                "competitionMatchDay": lineup.competition_match_day,
                "matchDayMapKey": lineup.match_day_map_key,
                "lineup": lineup.pack(),
                "substitutes": lineup.substitutes,
            },
        }
