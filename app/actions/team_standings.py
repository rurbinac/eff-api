from sqlalchemy.orm import Session
from app.models import TeamStanding


class TeamStandingsReadListAction:
    """Handle TeamStandings ReadList requests."""

    @staticmethod
    def execute(db: Session, team_id: int | None = None, league_id: int | None = None) -> list[dict]:
        """
        Get team standings filtered by team ID or league ID (pure data, no wrapper).

        Args:
            db: Database session
            team_id: Filter by teamID
            league_id: Filter by leagueID

        Returns:
            List of dicts with pure data (no response wrapper)
        """
        query = db.query(TeamStanding)

        if team_id is not None:
            query = query.filter(TeamStanding.teamID == team_id)
        elif league_id is not None:
            query = query.filter(TeamStanding.leagueID == league_id)

        standings = query.order_by(TeamStanding.place).all()

        items = []
        for standing in standings:
            values = {
                "teamStandingID": standing.teamStandingID,
                "leagueID": standing.leagueID,
                "divisionID": standing.divisionID,
                "teamID": standing.teamID,
                "userID": standing.userID,
                "season": standing.season,
                "seasonNum": standing.seasonNum,
                "matchDayMapKey": standing.matchDayMapKey,
                "realCompetitionID": standing.realCompetitionID,
                "realCompetitionMatchDay": standing.realCompetitionMatchDay,
                "competitionMatchDay": standing.competitionMatchDay,
                "lastCompetitionMatchDay": standing.lastCompetitionMatchDay,
                "teamName": standing.teamName,
                "place": standing.place,
                "won": standing.won,
                "draw": standing.draw,
                "lost": standing.lost,
                "scoreFor": standing.scoreFor,
                "scoreAgainst": standing.scoreAgainst,
                "points": standing.points,
                "wonHome": standing.wonHome,
                "drawHome": standing.drawHome,
                "lostHome": standing.lostHome,
                "scoreForHome": standing.scoreForHome,
                "scoreAgainstHome": standing.scoreAgainstHome,
                "pointsHome": standing.pointsHome,
                "wonAway": standing.wonAway,
                "drawAway": standing.drawAway,
                "lostAway": standing.lostAway,
                "scoreForAway": standing.scoreForAway,
                "scoreAgainstAway": standing.scoreAgainstAway,
                "pointsAway": standing.pointsAway,
                "createdBy": standing.createdBy,
                "createdIn": standing.createdIn.isoformat() if standing.createdIn else None,
                "updatedBy": standing.updatedBy,
                "updatedIn": standing.updatedIn.isoformat() if standing.updatedIn else None,
            }
            items.append(values)

        return items
