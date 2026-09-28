from sqlalchemy import select
from sqlalchemy.orm import Session

from app.guards import require_league_member
from app.models import Match, MatchTeam, Team


class TeamStandingsReadListAction:
    """Handle TeamStandings ReadList requests."""

    @staticmethod
    def execute(
        db: Session,
        user_id: int,
        team_id: int | None = None,
        league_id: int | None = None,
    ) -> list[dict]:
        stmt = (
            select(
                MatchTeam.matchTeamID.label("teamStandingID"),
                Team.leagueID,
                Team.divisionID,
                Team.teamID,
                Team.userID,
                Team.season,
                Team.seasonNum,
                Team.matchDayMapKey,
                Match.realCompetitionID,
                Match.realCompetitionMatchDay,
                Match.competitionMatchDay,
                Match.competitionLastMatchDay,
                Team.teamName,
                MatchTeam.place,
                MatchTeam.won,
                MatchTeam.draw,
                MatchTeam.lost,
                MatchTeam.scoreFor,
                MatchTeam.scoreAgainst,
                MatchTeam.points,
                MatchTeam.wonHome,
                MatchTeam.drawHome,
                MatchTeam.lostHome,
                MatchTeam.scoreForHome,
                MatchTeam.scoreAgainstHome,
                MatchTeam.pointsHome,
                MatchTeam.wonAway,
                MatchTeam.drawAway,
                MatchTeam.lostAway,
                MatchTeam.scoreForAway,
                MatchTeam.scoreAgainstAway,
                MatchTeam.pointsAway,
                MatchTeam.createdBy,
                MatchTeam.createdIn,
                MatchTeam.updatedBy,
                MatchTeam.updatedIn,
            )
            .join(Match, Match.matchID == MatchTeam.matchID)
            .join(Team, Team.teamID == MatchTeam.teamID)
            .order_by(MatchTeam.place.asc())
        )

        if team_id is not None:
            require_league_member(db, user_id, team_id=team_id)
            stmt = stmt.where(MatchTeam.teamID == team_id)
        elif league_id is not None:
            require_league_member(db, user_id, league_id=league_id)
            stmt = stmt.where(Team.leagueID == league_id)
        else:
            return []

        return [dict(row) for row in db.execute(stmt).mappings().all()]
