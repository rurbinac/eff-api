from sqlalchemy import text
from sqlalchemy.orm import Session

from app.guards import require_league_member


class TeamStandingsReadListAction:
    """Handle TeamStandings ReadList requests."""

    @staticmethod
    def execute(
        db: Session,
        user_id: int | None = None,
        team_id: int | None = None,
        league_id: int | None = None,
    ) -> list[dict]:
        base_query = """
            SELECT `mt`.`matchTeamID` AS `teamStandingID`,
                   `t`.`leagueID`,
                   `t`.`divisionID`,
                   `t`.`teamID`,
                   `t`.`userID`,
                   `t`.`season`,
                   `t`.`seasonNum`,
                   `t`.`matchDayMapKey`,
                   `m`.`realCompetitionID`,
                   `m`.`realCompetitionMatchDay`,
                   `m`.`competitionMatchDay`,
                   `m`.`competitionLastMatchDay`,
                   `t`.`teamName`,
                   `mt`.`place`,
                   `mt`.`won`,
                   `mt`.`draw`,
                   `mt`.`lost`,
                   `mt`.`scoreFor`,
                   `mt`.`scoreAgainst`,
                   `mt`.`points`,
                   `mt`.`wonHome`,
                   `mt`.`drawHome`,
                   `mt`.`lostHome`,
                   `mt`.`scoreForHome`,
                   `mt`.`scoreAgainstHome`,
                   `mt`.`pointsHome`,
                   `mt`.`wonAway`,
                   `mt`.`drawAway`,
                   `mt`.`lostAway`,
                   `mt`.`scoreForAway`,
                   `mt`.`scoreAgainstAway`,
                   `mt`.`pointsAway`,
                   `mt`.`createdBy`,
                   `mt`.`createdIn`,
                   `mt`.`updatedBy`,
                   `mt`.`updatedIn`
            FROM `MatchTeams` `mt`
            INNER JOIN `Matches` `m` ON `m`.`matchID` = `mt`.`matchID`
            INNER JOIN `Teams` `t` ON `t`.`teamID` = `mt`.`teamID`
            WHERE 1=1
        """

        params = {}

        if team_id is not None:
            require_league_member(db, user_id, team_id=team_id)
            base_query += " AND `mt`.`teamID` = :teamID"
            params["teamID"] = team_id
        elif league_id is not None:
            require_league_member(db, user_id, league_id=league_id)
            base_query += " AND `t`.`leagueID` = :leagueID"
            params["leagueID"] = league_id
        else:
            return []

        base_query += " ORDER BY `mt`.`place` ASC"

        result = db.execute(text(base_query), params)
        return [dict(row) for row in result.mappings().all()]
