from sqlalchemy.orm import Session
from sqlalchemy import text


class TeamStandingsReadListAction:
    """Handle TeamStandings ReadList requests."""

    @staticmethod
    def execute(db: Session, team_id: int | None = None, league_id: int | None = None) -> list[dict]:
        """
        Get team standings from MatchTeams and Matches (pure data, no wrapper).
        TeamStandings table was merged into MatchTeams, so this reconstructs it via JOIN.

        Args:
            db: Database session
            team_id: Filter by teamID
            league_id: Filter by leagueID

        Returns:
            List of dicts with pure data (no response wrapper)
        """
        # Build the standings query from MatchTeams + Matches
        base_query = """
            SELECT `t`.`matchTeamID` AS `leagueID`,
                   `m`.`leagueID`,
                   `m`.`divisionID`,
                   `t`.`teamID`,
                   `t`.`userID`,
                   `m`.`season`,
                   `m`.`seasonNum`,
                   `t`.`matchDayMapKey`,
                   `m`.`realCompetitionID`,
                   `m`.`realCompetitionMatchDay`,
                   `m`.`competitionMatchDay`,
                   `m`.`lastCompetitionMatchDay`,
                   `t`.`teamName`,
                   `t`.`place`,
                   `t`.`won`,
                   `t`.`draw`,
                   `t`.`lost`,
                   `t`.`scoreFor`,
                   `t`.`scoreAgainst`,
                   `t`.`points`,
                   `t`.`wonHome`,
                   `t`.`drawHome`,
                   `t`.`lostHome`,
                   `t`.`scoreForHome`,
                   `t`.`scoreAgainstHome`,
                   `t`.`pointsHome`,
                   `t`.`wonAway`,
                   `t`.`drawAway`,
                   `t`.`lostAway`,
                   `t`.`scoreForAway`,
                   `t`.`scoreAgainstAway`,
                   `t`.`pointsAway`,
                   `t`.`createdBy`,
                   `t`.`createdIn`,
                   `t`.`updatedBy`,
                   `t`.`updatedIn`
            FROM `MatchTeams` `t`
            LEFT OUTER JOIN `Matches` `m` ON `m`.`matchID` = `t`.`matchID`
            WHERE 1=1
        """

        params = {}

        # Add filters
        if team_id is not None:
            base_query += " AND `t`.`teamID` = :teamID"
            params["teamID"] = team_id
        elif league_id is not None:
            base_query += " AND `m`.`leagueID` = :leagueID"
            params["leagueID"] = league_id

        base_query += " ORDER BY `t`.`place` ASC"

        # Execute the query
        result = db.execute(text(base_query), params)
        rows = result.mappings().all()

        items = []
        for row in rows:
            values = dict(row)
            items.append(values)

        return items
