from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models import MatchTeam
from app.context import RequestContext


class MatchTeamsReadListAction:
    """Handle MatchTeams ReadList requests."""

    @staticmethod
    def execute(db: Session, team_id: int | None = None) -> dict:
        """
        Get match teams filtered by team ID.

        Args:
            db: Database session
            team_id: Filter by teamID (matches where this team is either participant)

        Returns:
            PHP-compatible response dict
        """
        query = db.query(MatchTeam)

        if team_id is not None:
            # Find all match teams where this team participated (as either first or second team)
            query = query.filter(
                or_(
                    MatchTeam.teamID == team_id,
                    MatchTeam.oppositeTeamID == team_id,
                )
            )
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
            values = {
                "matchTeamID": mt.matchTeamID,
                "matchID": mt.matchID,
                "matchTeamNum": mt.matchTeamNum,
                "matchStatus": mt.matchStatus,
                "leagueID": mt.leagueID,
                "divisionID": mt.divisionID,
                "season": mt.season,
                "seasonNum": mt.seasonNum,
                "realCompetitionID": mt.realCompetitionID,
                "realCompetitionMatchDay": mt.realCompetitionMatchDay,
                "realCompetitionMatchDaySort": mt.realCompetitionMatchDaySort,
                "competitionType": mt.competitionType,
                "competitionMatchDay": mt.competitionMatchDay,
                "competitionLastMatchDay": mt.competitionLastMatchDay,
                "competitionMatchNumber": mt.competitionMatchNumber,
                "competitionMatchGroup": mt.competitionMatchGroup,
                "competitionMatchNextGroup": mt.competitionMatchNextGroup,
                "competitionMatchRound": mt.competitionMatchRound,
                "competitionMatchLastRound": mt.competitionMatchLastRound,
                "matchGroupWinnerTeamID": mt.matchGroupWinnerTeamID,
                "userID": mt.userID,
                "teamID": mt.teamID,
                "teamName": mt.teamName,
                "teamScore": mt.teamScore,
                "teamPoints": mt.teamPoints,
                "teamSeeding": mt.teamSeeding,
                "matchDayMapKey": mt.matchDayMapKey,
                "oppositeUserID": mt.oppositeUserID,
                "oppositeTeamID": mt.oppositeTeamID,
                "oppositeTeamName": mt.oppositeTeamName,
                "oppositeTeamScore": mt.oppositeTeamScore,
                "oppositeTeamPoints": mt.oppositeTeamPoints,
                "oppositeTeamSeeding": mt.oppositeTeamSeeding,
                "oppositeMatchDayMapKey": mt.oppositeMatchDayMapKey,
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
