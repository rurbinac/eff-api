from datetime import datetime
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.context import RequestContext


class RealTeamStandingsReadListAction:
    """Handle RealTeamStandings ReadList requests."""

    @staticmethod
    def execute(
        db: Session,
        real_competition_id: int,
        real_competition_match_day: int,
    ) -> dict:
        """
        Get real team standings for a specific competition and match day.

        Args:
            db: Database session
            real_competition_id: Filter by realCompetitionID
            real_competition_match_day: Filter by realCompetitionMatchDay

        Returns:
            PHP-compatible response dict
        """
        query = """
            SELECT `realStandingID` AS `realTeamStandingID`,
                   `realTeamMemberID`,
                   `realTeamMemberKey`,
                   `realCompetitionID`,
                   `realCompetitionUID`,
                   `realCompetitionSYMID`,
                   `realCompetitionSeasonId`,
                   `realCompetitionMatchDay`,
                   `realCompetitionLastMatchDay`,
                   `baseRealCompetitionID`,
                   `extraRealCompetitionID`,
                   `realMatchStatus`,
                   `realTeamID`,
                   `realTeamUID`,
                   `realTeamName`,
                   `realTeamShortName`,
                   `position`,
                   `draftPosition`,
                   `draftPositionOrder`,
                   `place`,
                   (`won` + `draw` + `lost`) AS `played`,
                   `won`,
                   `draw`,
                   `lost`,
                   ((3 * `won`) + `draw`) AS `points`,
                   `goalsFor`,
                   `goalsAgainst`,
                   `placeHome`,
                   (`wonHome` + `drawHome` + `lostHome`) AS `playedHome`,
                   `wonHome`,
                   `drawHome`,
                   `lostHome`,
                   ((3 * `wonHome`) + `drawHome`) AS `pointsHome`,
                   `goalsForHome`,
                   `goalsAgainstHome`,
                   `placeAway`,
                   (`wonAway` + `drawAway` + `lostAway`) AS `playedAway`,
                   `wonAway`,
                   `drawAway`,
                   `lostAway`,
                   ((3 * `wonAway`) + `drawAway`) AS `pointsAway`,
                   `goalsForAway`,
                   `goalsAgainstAway`,
                   `createdIn`,
                   `updatedIn`
            FROM `RealStandings`
            WHERE `isTeam` = 1
              AND `realCompetitionID` = :realCompetitionID
              AND `realCompetitionMatchDay` = :realCompetitionMatchDay
            ORDER BY `place` ASC
        """

        result = db.execute(
            text(query),
            {
                "realCompetitionID": real_competition_id,
                "realCompetitionMatchDay": real_competition_match_day,
            },
        )

        def to_iso(dt):
            if dt is None:
                return None
            if isinstance(dt, str):
                return dt
            return dt.isoformat()

        items = []
        for row in result:
            values = {
                "realTeamStandingID": row[0],
                "realTeamMemberID": row[1],
                "realTeamMemberKey": row[2],
                "realCompetitionID": row[3],
                "realCompetitionUID": row[4],
                "realCompetitionSYMID": row[5],
                "realCompetitionSeasonId": row[6],
                "realCompetitionMatchDay": row[7],
                "realCompetitionLastMatchDay": row[8],
                "baseRealCompetitionID": row[9],
                "extraRealCompetitionID": row[10],
                "realMatchStatus": row[11],
                "realTeamID": row[12],
                "realTeamUID": row[13],
                "realTeamName": row[14],
                "realTeamShortName": row[15],
                "position": row[16],
                "draftPosition": row[17],
                "draftPositionOrder": row[18],
                "place": row[19],
                "played": row[20],
                "won": row[21],
                "draw": row[22],
                "lost": row[23],
                "points": row[24],
                "goalsFor": row[25],
                "goalsAgainst": row[26],
                "placeHome": row[27],
                "playedHome": row[28],
                "wonHome": row[29],
                "drawHome": row[30],
                "lostHome": row[31],
                "pointsHome": row[32],
                "goalsForHome": row[33],
                "goalsAgainstHome": row[34],
                "placeAway": row[35],
                "playedAway": row[36],
                "wonAway": row[37],
                "drawAway": row[38],
                "lostAway": row[39],
                "pointsAway": row[40],
                "goalsForAway": row[41],
                "goalsAgainstAway": row[42],
                "createdIn": to_iso(row[43]),
                "updatedIn": to_iso(row[44]),
            }
            items.append({"values": values})

        return {
            "table": "RealTeamStandings",
            "timestamp": RequestContext.get_datetime().strftime("%Y-%m-%d %H:%M:%S"),
            "items": items,
        }
