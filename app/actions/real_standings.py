from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models import RealStanding
from app.context import RequestContext


class RealStandingsReadListAction:
    """Handle RealStandings ReadList requests."""

    @staticmethod
    def execute(
        db: Session,
        real_competition_id: int,
        real_competition_match_day: int,
        division_id: int | None = None,
    ) -> dict:
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
            # Convert to dict for modification
            row = {
                "realStandingID": standing.realStandingID,
                "realTeamMemberID": standing.realTeamMemberID,
                "realTeamMemberKey": standing.realTeamMemberKey,
                "prevRealTeamMemberKey": standing.prevRealTeamMemberKey,
                "nextRealTeamMemberKey": standing.nextRealTeamMemberKey,
                "realCompetitionID": standing.realCompetitionID,
                "realCompetitionUID": standing.realCompetitionUID,
                "realCompetitionSYMID": standing.realCompetitionSYMID,
                "realCompetitionSeasonId": standing.realCompetitionSeasonId,
                "realCompetitionMatchDay": standing.realCompetitionMatchDay,
                "realCompetitionLastMatchDay": standing.realCompetitionLastMatchDay,
                "baseRealCompetitionID": standing.baseRealCompetitionID,
                "extraRealCompetitionID": standing.extraRealCompetitionID,
                "isTeam": standing.isTeam,
                "isPlayer": standing.isPlayer,
                "baseMatchDay": standing.baseMatchDay,
                "realMatchID": standing.realMatchID,
                "realMatchTeamID": standing.realMatchTeamID,
                "realMatchDate": standing.realMatchDate.isoformat() if standing.realMatchDate else None,
                "realMatchTime": standing.realMatchTime,
                "realMatchStatus": standing.realMatchStatus,
                "realTeamID": standing.realTeamID,
                "realTeamUID": standing.realTeamUID,
                "realTeamName": standing.realTeamName,
                "realTeamShortName": standing.realTeamShortName,
                "realTeamScore": standing.realTeamScore,
                "realTeamSide": standing.realTeamSide,
                "oppositeRealTeamID": standing.oppositeRealTeamID,
                "oppositeRealTeamUID": standing.oppositeRealTeamUID,
                "oppositeRealTeamName": standing.oppositeRealTeamName,
                "oppositeRealTeamShortName": standing.oppositeRealTeamShortName,
                "oppositeRealTeamScore": standing.oppositeRealTeamScore,
                "realPlayerID": standing.realPlayerID,
                "realPlayerUID": standing.realPlayerUID,
                "firstName": standing.firstName,
                "lastName": standing.lastName,
                "knownName": standing.knownName,
                "name": standing.name,
                "sortName": standing.sortName,
                "position": standing.position,
                "draftPosition": standing.draftPosition,
                "draftPositionOrder": standing.draftPositionOrder,
                "timePlayed": standing.timePlayed,
                "gamePlayed": standing.gamePlayed,
                "goals": standing.goals,
                "assists": standing.assists,
                "yellowCards": standing.yellowCards,
                "redCards": standing.redCards,
                "goalsConceded": standing.goalsConceded,
                "cleanSheet": standing.cleanSheet,
                "matchTimePlayed": standing.matchTimePlayed,
                "matchGamePlayed": standing.matchGamePlayed,
                "matchGoals": standing.matchGoals,
                "matchAssists": standing.matchAssists,
                "matchYellowCards": standing.matchYellowCards,
                "matchRedCards": standing.matchRedCards,
                "matchGoalsConceded": standing.matchGoalsConceded,
                "matchCleanSheet": standing.matchCleanSheet,
                "matchDayPlayed": standing.matchDayPlayed,
                "matchWon": standing.matchWon,
                "matchDraw": standing.matchDraw,
                "matchLost": standing.matchLost,
                "played": standing.played,
                "won": standing.won,
                "draw": standing.draw,
                "lost": standing.lost,
                "goalsFor": standing.goalsFor,
                "goalsAgainst": standing.goalsAgainst,
                "place": standing.place,
                "playedHome": standing.playedHome,
                "wonHome": standing.wonHome,
                "drawHome": standing.drawHome,
                "lostHome": standing.lostHome,
                "goalsForHome": standing.goalsForHome,
                "goalsAgainstHome": standing.goalsAgainstHome,
                "placeHome": standing.placeHome,
                "playedAway": standing.playedAway,
                "wonAway": standing.wonAway,
                "drawAway": standing.drawAway,
                "lostAway": standing.lostAway,
                "goalsForAway": standing.goalsForAway,
                "goalsAgainstAway": standing.goalsAgainstAway,
                "placeAway": standing.placeAway,
                "matchPointsL1Played": standing.matchPointsL1Played,
                "matchPointsL1GoalsAllowed": standing.matchPointsL1GoalsAllowed,
                "matchPointsL1CleanSheet": standing.matchPointsL1CleanSheet,
                "matchPointsL1Cards": standing.matchPointsL1Cards,
                "matchPointsL1Goals": standing.matchPointsL1Goals,
                "matchPointsL1Assists": standing.matchPointsL1Assists,
                "matchPointsL1OwnGoals": standing.matchPointsL1OwnGoals,
                "matchPointsL1": standing.matchPointsL1,
                "pointsL1Played": standing.pointsL1Played,
                "pointsL1GoalsAllowed": standing.pointsL1GoalsAllowed,
                "pointsL1CleanSheet": standing.pointsL1CleanSheet,
                "pointsL1Cards": standing.pointsL1Cards,
                "pointsL1Goals": standing.pointsL1Goals,
                "pointsL1Assists": standing.pointsL1Assists,
                "pointsL1OwnGoals": standing.pointsL1OwnGoals,
                "pointsL1": standing.pointsL1,
                "livePointsL1": standing.livePointsL1,
                "ranking": standing.ranking,
                "processed": standing.processed,
                "createdIn": standing.createdIn.isoformat() if standing.createdIn else None,
                "updatedIn": standing.updatedIn.isoformat() if standing.updatedIn else None,
            }

            # Add fantasy team enrichment if division_id provided
            if division_id is not None:
                row = RealStandingsReadListAction._enrich_with_team_data(
                    row, standing.realTeamMemberKey, teams_map
                )

            items.append({"values": row})

        return {
            "table": "RealStandings",
            "timestamp": RequestContext.get_datetime().strftime("%Y-%m-%d %H:%M:%S"),
            "items": items,
        }

    @staticmethod
    def _load_teams(db: Session, division_id: int) -> dict:
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
    ) -> dict:
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
