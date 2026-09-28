from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import RealStanding
from app.utils.dt import to_iso


class RealTeamStandingsReadListAction:
    """Handle RealTeamStandings ReadList requests."""

    @staticmethod
    def execute(
        db: Session,
        real_competition_id: int,
        real_competition_match_day: int,
    ) -> list[dict]:
        stmt = (
            select(
                RealStanding.realStandingID.label("realTeamStandingID"),
                RealStanding.realTeamMemberID,
                RealStanding.realTeamMemberKey,
                RealStanding.realCompetitionID,
                RealStanding.realCompetitionUID,
                RealStanding.realCompetitionSYMID,
                RealStanding.realCompetitionSeasonId,
                RealStanding.realCompetitionMatchDay,
                RealStanding.realCompetitionLastMatchDay,
                RealStanding.baseRealCompetitionID,
                RealStanding.extraRealCompetitionID,
                RealStanding.realMatchStatus,
                RealStanding.realTeamID,
                RealStanding.realTeamUID,
                RealStanding.realTeamName,
                RealStanding.realTeamShortName,
                RealStanding.position,
                RealStanding.draftPosition,
                RealStanding.draftPositionOrder,
                RealStanding.place,
                RealStanding.played,
                RealStanding.won,
                RealStanding.draw,
                RealStanding.lost,
                (3 * RealStanding.won + RealStanding.draw).label("points"),
                RealStanding.goalsFor,
                RealStanding.goalsAgainst,
                RealStanding.placeHome,
                RealStanding.playedHome,
                RealStanding.wonHome,
                RealStanding.drawHome,
                RealStanding.lostHome,
                (3 * RealStanding.wonHome + RealStanding.drawHome).label("pointsHome"),
                RealStanding.goalsForHome,
                RealStanding.goalsAgainstHome,
                RealStanding.placeAway,
                RealStanding.playedAway,
                RealStanding.wonAway,
                RealStanding.drawAway,
                RealStanding.lostAway,
                (3 * RealStanding.wonAway + RealStanding.drawAway).label("pointsAway"),
                RealStanding.goalsForAway,
                RealStanding.goalsAgainstAway,
                RealStanding.createdIn,
                RealStanding.updatedIn,
            )
            .where(
                RealStanding.isTeam == 1,
                RealStanding.realCompetitionID == real_competition_id,
                RealStanding.realCompetitionMatchDay == real_competition_match_day,
            )
            .order_by(RealStanding.place.asc())
        )

        return [
            {**dict(row), "createdIn": to_iso(row["createdIn"]), "updatedIn": to_iso(row["updatedIn"])}
            for row in db.execute(stmt).mappings().all()
        ]
