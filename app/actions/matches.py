from sqlalchemy.orm import Session
from app.models import Match, MatchTeam


class MatchesReadListAction:
    """Handle Matches ReadList requests."""

    @staticmethod
    def execute(
        db: Session,
        league_id: int | None = None,
        division_id: int | None = None,
    ) -> list[dict]:
        """
        Get fantasy league matches filtered by league or division ID.
        Joins with MatchTeams to reconstruct team-specific fields.

        Args:
            db: Database session
            league_id: Filter by leagueID
            division_id: Filter by divisionID

        Returns:
            List of match dicts with first/second team fields
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
            # Query MatchTeams for this match to get team data
            team_records = db.query(MatchTeam).filter(
                MatchTeam.matchID == match.matchID
            ).all()

            # Create a dict keyed by matchTeamNum
            teams_by_num = {mt.matchTeamNum: mt for mt in team_records}

            def to_iso(dt):
                if dt is None:
                    return None
                if isinstance(dt, str):
                    return dt
                return dt.isoformat()

            # Build values dict with match metadata and pivoted team data
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
            }

            # Add first team data (matchTeamNum = 1)
            if 1 in teams_by_num:
                mt1 = teams_by_num[1]
                values.update({
                    "firstUserID": mt1.userID,
                    "firstTeamID": mt1.teamID,
                    "firstTeamName": mt1.teamName,
                    "firstTeamScore": mt1.teamScore,
                    "firstTeamPoints": mt1.teamPoints,
                    "firstTeamSeeding": mt1.teamSeeding,
                    "firstMatchDayMapKey": mt1.matchDayMapKey,
                })
            else:
                values.update({
                    "firstUserID": None,
                    "firstTeamID": None,
                    "firstTeamName": None,
                    "firstTeamScore": None,
                    "firstTeamPoints": None,
                    "firstTeamSeeding": None,
                    "firstMatchDayMapKey": None,
                })

            # Add second team data (matchTeamNum = 2)
            if 2 in teams_by_num:
                mt2 = teams_by_num[2]
                values.update({
                    "secondUserID": mt2.userID,
                    "secondTeamID": mt2.teamID,
                    "secondTeamName": mt2.teamName,
                    "secondTeamScore": mt2.teamScore,
                    "secondTeamPoints": mt2.teamPoints,
                    "secondTeamSeeding": mt2.teamSeeding,
                    "secondMatchDayMapKey": mt2.matchDayMapKey,
                })
            else:
                values.update({
                    "secondUserID": None,
                    "secondTeamID": None,
                    "secondTeamName": None,
                    "secondTeamScore": None,
                    "secondTeamPoints": None,
                    "secondTeamSeeding": None,
                    "secondMatchDayMapKey": None,
                })

            # Add metadata
            values.update({
                "createdBy": match.createdBy,
                "createdIn": to_iso(match.createdIn),
                "updatedBy": match.updatedBy,
                "updatedIn": to_iso(match.updatedIn),
            })

            items.append({"values": values})

        return items
