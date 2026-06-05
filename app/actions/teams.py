from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models import Team
from app.context import RequestContext
from app.utils import MKeys


class TeamsGetRealMembersRankingAction:
    """Get real members ranking for a team."""

    @staticmethod
    def execute(db: Session, team_id: int) -> list[dict]:
        """Get real members with ranking metadata (pure data, no wrapper)."""
        # Query target team's ranking info
        team_stmt = text("""
            SELECT `teamID`, `baseRealCompetitionID`, `membersRanking`, `teamMembers`, `divisionID`
            FROM `Teams`
            WHERE `teamID` = :teamID
            LIMIT 1
        """)
        team_result = db.execute(team_stmt, {"teamID": team_id})
        team_row = team_result.mappings().first()

        if not team_row:
            return []

        target_team = dict(team_row)
        base_competition_id = target_team["baseRealCompetitionID"]
        division_id = target_team["divisionID"]
        members_ranking_str = target_team["membersRanking"] or ""
        team_members_str = target_team["teamMembers"] or ""

        # Get other teams in division to build division roster
        division_teams_stmt = text("""
            SELECT `teamMembers`
            FROM `Teams`
            WHERE `divisionID` = :divisionID
              AND `teamID` != :teamID
        """)
        division_teams_result = db.execute(
            division_teams_stmt,
            {"divisionID": division_id, "teamID": team_id}
        )
        division_teams = [dict(row) for row in division_teams_result.mappings()]

        # Build division roster by concatenating all team members
        team_members_div_parts = [row.get("teamMembers") or "" for row in division_teams]
        team_members_div = ":".join([p for p in team_members_div_parts if p])

        # Parse ranking using MKeys
        ranking_keys = MKeys(members_ranking_str, size=1)
        keys = ranking_keys.get_group(0)

        # Create dict with ranking keys mapped to None initially
        my_dict = dict.fromkeys(keys, None)

        # Create MKeys for team and division membership
        team_mkeys = MKeys(team_members_str, size=1)
        division_mkeys = MKeys(team_members_div, size=1) if team_members_div else MKeys(".", size=1)

        # Query real team members ordered by ranking and name
        members_stmt = text("""
            SELECT *
            FROM `RealTeamMembers`
            WHERE `enabled` = 1
              AND `baseRealCompetitionID` = :baseRealCompetitionID
            ORDER BY IFNULL(`last_ranking`, 1000000000), `name`
        """)
        members_result = db.execute(
            members_stmt,
            {"baseRealCompetitionID": base_competition_id}
        )

        # Process each member
        for row in members_result.mappings():
            member_dict = dict(row)
            member_key = member_dict.get("realTeamMemberKey")

            # Add membership flags
            member_dict["inTeam"] = 1 if member_key in team_mkeys.get_group(0) else 0
            member_dict["inDivision"] = 1 if member_key in division_mkeys.get_group(0) else 0
            member_dict["inRanking"] = 1 if member_key in my_dict else 0

            # Populate dict if member is in ranking
            if member_key in my_dict:
                my_dict[member_key] = member_dict

        # Return non-None values, preserving ranking order
        result = [v for v in my_dict.values() if v is not None]
        return result


class TeamsReadListAction:
    """Get teams for a league or division."""

    @staticmethod
    def execute(
        db: Session,
        league_id: int | None = None,
        division_id: int | None = None,
    ) -> list[dict]:
        """Get teams filtered by league ID or division ID (pure data, no wrapper)."""
        # Query teams based on filter
        query = db.query(Team)

        if league_id is not None:
            query = query.filter(Team.leagueID == league_id)
        elif division_id is not None:
            query = query.filter(Team.divisionID == division_id)
        else:
            # If no filter provided, return empty
            query = query.filter(False)

        teams = query.all()

        # Convert to dicts with all fields
        items = []
        for team in teams:
            row = {
                "teamID": team.teamID,
                "baseRealCompetitionID": team.baseRealCompetitionID,
                "extraRealCompetitionID": team.extraRealCompetitionID,
                "matchDayMapKey": team.matchDayMapKey,
                "leagueID": team.leagueID,
                "divisionID": team.divisionID,
                "commissionerID": team.commissionerID,
                "userID": team.userID,
                "prevLeagueID": team.prevLeagueID,
                "nextLeagueID": team.nextLeagueID,
                "prevDivisionID": team.prevDivisionID,
                "nextDivisionID": team.nextDivisionID,
                "prevTeamID": team.prevTeamID,
                "nextTeamID": team.nextTeamID,
                "season": team.season,
                "seasonNum": team.seasonNum,
                "leagueMatches": team.leagueMatches,
                "divisionMatches": team.divisionMatches,
                "draftOrder": team.draftOrder,
                "randomOrder": team.randomOrder,
                "waiversOrder": team.waiversOrder,
                "teamName": team.teamName,
                "teamAvatar": team.teamAvatar,
                "teamMembers": team.teamMembers,
                "draftMembers": team.draftMembers,
                "membersRanking": team.membersRanking,
                "membersWaivers": team.membersWaivers,
                "membersWishList": team.membersWishList,
                "franchiseWishList": team.franchiseWishList,
                "fantasyPoints": team.fantasyPoints,
                "teamRanking": team.teamRanking,
                "locked": team.locked,
                "isCommissioner": team.isCommissioner,
                "cntEPLTeam": team.cntEPLTeam,
                "cntPlayer": team.cntPlayer,
                "cntGoalkeeper": team.cntGoalkeeper,
                "cntDefender": team.cntDefender,
                "cntMidfielder": team.cntMidfielder,
                "cntStriker": team.cntStriker,
                "cntAdd": team.cntAdd,
                "cntDrop": team.cntDrop,
                "cntWaiver": team.cntWaiver,
                "notes": team.notes,
                "place": team.place,
                "points": team.points,
                "statusC1": team.statusC1,
                "statusC2": team.statusC2,
                "statusC3": team.statusC3,
                "seedingC1": team.seedingC1,
                "seedingC2": team.seedingC2,
                "seedingC3": team.seedingC3,
                "createdBy": team.createdBy,
                "createdIn": team.createdIn.isoformat() if team.createdIn else None,
                "updatedBy": team.updatedBy,
                "updatedIn": team.updatedIn.isoformat() if team.updatedIn else None,
            }
            items.append(row)

        # Return pure data (no response wrapper)
        return items
