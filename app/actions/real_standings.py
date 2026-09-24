from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models import RealStanding
from app.utils.dt import to_iso


class RealStandingsReadListAction:
    """Handle RealStandings ReadList requests."""

    @staticmethod
    def execute_by_member_key(
        db: Session,
        real_competition_id: int,
        real_team_member_key: str,
        include: list[str] | None = None,
    ) -> list[dict]:
        """Get all match-day standings for a single realTeamMemberKey in a competition."""
        standings = (
            db.query(RealStanding)
            .filter(
                RealStanding.realCompetitionID == real_competition_id,
                RealStanding.realTeamMemberKey == real_team_member_key,
            )
            .order_by(RealStanding.realCompetitionMatchDay)
            .all()
        )
        rows = [RealStandingsReadListAction._to_dict(s) for s in standings]
        if include:
            rows = [{k: r[k] for k in include if k in r} for r in rows]
        return rows

    @staticmethod
    def execute(
        db: Session,
        real_competition_id: int,
        real_competition_match_day: int,
        division_id: int | None = None,
    ) -> list[dict]:
        """
        Get real standings filtered by competition and match day.
        If division_id is provided, enriches each row with fantasy team data.

        Args:
            db: Database session
            real_competition_id: Filter by realCompetitionID
            real_competition_match_day: Filter by realCompetitionMatchDay
            division_id: Optional division ID to enrich with fantasy team data

        Returns:
            PHP-compatible response dict
        """
        # Load teams for the division if provided
        teams_map = {}
        if division_id is not None:
            teams_map = RealStandingsReadListAction._load_teams(db, division_id)

        # Query RealStandings
        standings = db.query(RealStanding).filter(
            RealStanding.realCompetitionID == real_competition_id,
            RealStanding.realCompetitionMatchDay == real_competition_match_day,
        ).all()

        items = []
        for standing in standings:
            row = RealStandingsReadListAction._to_dict(standing)
            if division_id is not None:
                row = RealStandingsReadListAction._enrich_with_team_data(
                    row, standing.realTeamMemberKey, teams_map
                )
            items.append(row)

        return items

    @staticmethod
    def _to_dict(s: RealStanding) -> dict:
        return {
            "realStandingID": s.realStandingID,
            "realTeamMemberID": s.realTeamMemberID,
            "realTeamMemberKey": s.realTeamMemberKey,
            "prevRealTeamMemberKey": s.prevRealTeamMemberKey,
            "nextRealTeamMemberKey": s.nextRealTeamMemberKey,
            "realCompetitionID": s.realCompetitionID,
            "realCompetitionUID": s.realCompetitionUID,
            "realCompetitionSYMID": s.realCompetitionSYMID,
            "realCompetitionSeasonId": s.realCompetitionSeasonId,
            "realCompetitionMatchDay": s.realCompetitionMatchDay,
            "realCompetitionLastMatchDay": s.realCompetitionLastMatchDay,
            "baseRealCompetitionID": s.baseRealCompetitionID,
            "extraRealCompetitionID": s.extraRealCompetitionID,
            "isTeam": s.isTeam,
            "isPlayer": s.isPlayer,
            "baseMatchDay": s.baseMatchDay,
            "realMatchID": s.realMatchID,
            "realMatchTeamID": s.realMatchTeamID,
            "realMatchDate": to_iso(s.realMatchDate),
            "realMatchTime": s.realMatchTime,
            "realMatchStatus": s.realMatchStatus,
            "realTeamID": s.realTeamID,
            "realTeamUID": s.realTeamUID,
            "realTeamName": s.realTeamName,
            "realTeamShortName": s.realTeamShortName,
            "realTeamScore": s.realTeamScore,
            "realTeamSide": s.realTeamSide,
            "oppositeRealTeamID": s.oppositeRealTeamID,
            "oppositeRealTeamUID": s.oppositeRealTeamUID,
            "oppositeRealTeamName": s.oppositeRealTeamName,
            "oppositeRealTeamShortName": s.oppositeRealTeamShortName,
            "oppositeRealTeamScore": s.oppositeRealTeamScore,
            "realPlayerID": s.realPlayerID,
            "realPlayerUID": s.realPlayerUID,
            "firstName": s.firstName,
            "lastName": s.lastName,
            "knownName": s.knownName,
            "name": s.name,
            "sortName": s.sortName,
            "position": s.position,
            "draftPosition": s.draftPosition,
            "draftPositionOrder": s.draftPositionOrder,
            "timePlayed": s.timePlayed,
            "gamePlayed": s.gamePlayed,
            "goals": s.goals,
            "assists": s.assists,
            "yellowCards": s.yellowCards,
            "redCards": s.redCards,
            "goalsConceded": s.goalsConceded,
            "cleanSheet": s.cleanSheet,
            "matchTimePlayed": s.matchTimePlayed,
            "matchGamePlayed": s.matchGamePlayed,
            "matchGoals": s.matchGoals,
            "matchAssists": s.matchAssists,
            "matchYellowCards": s.matchYellowCards,
            "matchRedCards": s.matchRedCards,
            "matchGoalsConceded": s.matchGoalsConceded,
            "matchCleanSheet": s.matchCleanSheet,
            "matchDayPlayed": s.matchDayPlayed,
            "matchWon": s.matchWon,
            "matchDraw": s.matchDraw,
            "matchLost": s.matchLost,
            "played": s.played,
            "won": s.won,
            "draw": s.draw,
            "lost": s.lost,
            "goalsFor": s.goalsFor,
            "goalsAgainst": s.goalsAgainst,
            "place": s.place,
            "playedHome": s.playedHome,
            "wonHome": s.wonHome,
            "drawHome": s.drawHome,
            "lostHome": s.lostHome,
            "goalsForHome": s.goalsForHome,
            "goalsAgainstHome": s.goalsAgainstHome,
            "placeHome": s.placeHome,
            "playedAway": s.playedAway,
            "wonAway": s.wonAway,
            "drawAway": s.drawAway,
            "lostAway": s.lostAway,
            "goalsForAway": s.goalsForAway,
            "goalsAgainstAway": s.goalsAgainstAway,
            "placeAway": s.placeAway,
            "matchPointsL1Played": s.matchPointsL1Played,
            "matchPointsL1GoalsAllowed": s.matchPointsL1GoalsAllowed,
            "matchPointsL1CleanSheet": s.matchPointsL1CleanSheet,
            "matchPointsL1Cards": s.matchPointsL1Cards,
            "matchPointsL1Goals": s.matchPointsL1Goals,
            "matchPointsL1Assists": s.matchPointsL1Assists,
            "matchPointsL1OwnGoals": s.matchPointsL1OwnGoals,
            "matchPointsL1": s.matchPointsL1,
            "pointsL1Played": s.pointsL1Played,
            "pointsL1GoalsAllowed": s.pointsL1GoalsAllowed,
            "pointsL1CleanSheet": s.pointsL1CleanSheet,
            "pointsL1Cards": s.pointsL1Cards,
            "pointsL1Goals": s.pointsL1Goals,
            "pointsL1Assists": s.pointsL1Assists,
            "pointsL1OwnGoals": s.pointsL1OwnGoals,
            "pointsL1": s.pointsL1,
            "livePointsL1": s.livePointsL1,
            "ranking": s.ranking,
            "processed": s.processed,
            "createdIn": to_iso(s.createdIn),
            "updatedIn": to_iso(s.updatedIn),
        }

    @staticmethod
    def _load_teams(db: Session, division_id: int) -> list[dict]:
        """
        Load teams for a division and create a map keyed by teamMembers string.

        Returns:
            dict mapping teamMembers string to team data dict
        """
        teams_map = {}
        result = db.execute(
            text("""
                SELECT teamID, teamName, teamMembers, fantasyPoints, isCommissioner
                FROM Teams
                WHERE divisionID = :divisionID
            """),
            {"divisionID": division_id},
        )

        for row in result:
            team_members_str = row[2]  # teamMembers
            team_data = {
                "teamID": row[0],
                "teamName": row[1],
                "fantasyPoints": row[3],
                "isCommissioner": row[4],
            }
            teams_map[team_members_str] = team_data

        return teams_map

    @staticmethod
    def _enrich_with_team_data(
        row: dict, real_team_member_key: str, teams_map: dict
    ) -> list[dict]:
        """
        Enrich a RealStandings row with fantasy team data.
        Looks for the real member key in team members strings.

        Args:
            row: RealStandings row as dict
            real_team_member_key: The realTeamMemberKey to search for
            teams_map: Map of teamMembers strings to team data

        Returns:
            Enriched row with teamID, teamName, fantasyPoints, isCommissioner
        """
        row["teamID"] = None
        row["teamName"] = None
        row["fantasyPoints"] = None
        row["isCommissioner"] = None

        search_key = real_team_member_key + "."
        for team_members_str, team_data in teams_map.items():
            if search_key in team_members_str:
                row["teamID"] = team_data["teamID"]
                row["teamName"] = team_data["teamName"]
                row["fantasyPoints"] = team_data["fantasyPoints"]
                row["isCommissioner"] = team_data["isCommissioner"]
                break

        return row
