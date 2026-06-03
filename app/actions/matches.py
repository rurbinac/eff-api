from datetime import datetime
from sqlalchemy.orm import Session
from app.models import Match
from app.context import RequestContext


class MatchesReadListAction:
    """Handle Matches ReadList requests."""

    @staticmethod
    def execute(
        db: Session,
        league_id: int | None = None,
        division_id: int | None = None,
    ) -> dict:
        """
        Get fantasy league matches filtered by league or division ID.

        Args:
            db: Database session
            league_id: Filter by leagueID
            division_id: Filter by divisionID

        Returns:
            PHP-compatible response dict
        """
        query = db.query(Match)

        if league_id is not None:
            query = query.filter(Match.leagueID == league_id)
        elif division_id is not None:
            query = query.filter(Match.divisionID == division_id)
        else:
            query = query.filter(False)

        matches = query.order_by(Match.matchID).all()

        items = []
        for match in matches:
            def to_iso(dt):
                if dt is None:
                    return None
                if isinstance(dt, str):
                    return dt
                return dt.isoformat()

            values = {
                "matchID": match.matchID,
                "matchStatus": match.matchStatus,
                "leagueID": match.leagueID,
                "divisionID": match.divisionID,
                "season": match.season,
                "seasonNum": match.seasonNum,
                "realCompetitionID": match.realCompetitionID,
                "realCompetitionMatchDay": match.realCompetitionMatchDay,
                "realCompetitionMatchDaySort": match.realCompetitionMatchDaySort,
                "competitionType": match.competitionType,
                "competitionMatchDay": match.competitionMatchDay,
                "competitionLastMatchDay": match.competitionLastMatchDay,
                "competitionMatchNumber": match.competitionMatchNumber,
                "competitionMatchGroup": match.competitionMatchGroup,
                "competitionMatchNextGroup": match.competitionMatchNextGroup,
                "competitionMatchRound": match.competitionMatchRound,
                "competitionMatchLastRound": match.competitionMatchLastRound,
                "matchGroupWinnerTeamID": match.matchGroupWinnerTeamID,
                "firstUserID": match.firstUserID,
                "firstTeamID": match.firstTeamID,
                "firstTeamName": match.firstTeamName,
                "firstTeamScore": match.firstTeamScore,
                "firstTeamPoints": match.firstTeamPoints,
                "firstTeamSeeding": match.firstTeamSeeding,
                "firstMatchDayMapKey": match.firstMatchDayMapKey,
                "secondUserID": match.secondUserID,
                "secondTeamID": match.secondTeamID,
                "secondTeamName": match.secondTeamName,
                "secondTeamScore": match.secondTeamScore,
                "secondTeamPoints": match.secondTeamPoints,
                "secondTeamSeeding": match.secondTeamSeeding,
                "secondMatchDayMapKey": match.secondMatchDayMapKey,
                "createdBy": match.createdBy,
                "createdIn": to_iso(match.createdIn),
                "updatedBy": match.updatedBy,
                "updatedIn": to_iso(match.updatedIn),
            }
            items.append({"values": values})

        return {
            "table": "Matches",
            "timestamp": RequestContext.get_datetime().strftime("%Y-%m-%d %H:%M:%S"),
            "items": items,
        }
