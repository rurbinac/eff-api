from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models import Team
from app.context import RequestContext
from app.utils import MKeys


class TeamsGetCurrentMembersAction:
    """Get current team members with real stats in roster order."""

    @staticmethod
    def execute(db: Session, team_id: int) -> list[dict]:
        """Get team members ordered by teamMembers field (pure data, no wrapper)."""
        # Query team to get members string and competition ID
        team_stmt = text("""
            SELECT `teamMembers`, `baseRealCompetitionID`
            FROM `Teams`
            WHERE `teamID` = :teamID
            LIMIT 1
        """)
        team_result = db.execute(team_stmt, {"teamID": team_id})
        team_row = team_result.mappings().first()

        if not team_row:
            return []

        team_members_str = team_row.get("teamMembers") or ""
        base_competition_id = team_row.get("baseRealCompetitionID")

        if not team_members_str or not base_competition_id:
            return []

        # Parse team members using MKeys
        team_mkeys = MKeys.build(team_members_str, size=1)
        if not team_mkeys:
            return []

        keys = team_mkeys.get_group(0)
        if not keys:
            return []

        # Create dict with keys in order, initialized to None
        my_dict = dict.fromkeys(keys, None)

        # Query real team members
        members_stmt = text("""
            SELECT *
            FROM `RealTeamMembers`
            WHERE `baseRealCompetitionID` = :baseRealCompetitionID
              AND `realTeamMemberKey` IN (:keys)
        """)
        members_result = db.execute(
            members_stmt,
            {"baseRealCompetitionID": base_competition_id, "keys": keys}
        )

        # Populate dict with members
        for row in members_result.mappings():
            member_dict = dict(row)
            member_key = member_dict.get("realTeamMemberKey")
            if member_key in my_dict:
                my_dict[member_key] = member_dict

        # Return non-None values in order
        result = [v for v in my_dict.values() if v is not None]
        return result


class TeamsSetFranchiseWishListAction:
    """Set team's franchise wish list."""

    @staticmethod
    def execute(db: Session, team_id: int, user_id: int, franchise_wish_list_keys_str: str) -> dict:
        """Set team's franchise wish list (pure data, no wrapper)."""
        # Query team to verify it exists and get owner
        team_stmt = text("""
            SELECT `userID`
            FROM `Teams`
            WHERE `teamID` = :teamID
            LIMIT 1
        """)
        team_result = db.execute(team_stmt, {"teamID": team_id})
        team_row = team_result.mappings().first()

        if not team_row:
            raise Exception(f"Team {team_id} not found")

        team_user_id = team_row["userID"]
        if team_user_id != user_id:
            raise Exception("Unauthorized: You do not own this team")

        # Parse franchise wish list keys - handle both dot and comma separated formats
        if "." in franchise_wish_list_keys_str and "," not in franchise_wish_list_keys_str:
            wish_keys = [k.strip() for k in franchise_wish_list_keys_str.split(".") if k.strip()]
        else:
            wish_keys = [k.strip() for k in franchise_wish_list_keys_str.split(",") if k.strip()]

        # Build MKeys with list and pack
        mkeys = MKeys.build([wish_keys], size=1)
        if not mkeys:
            raise Exception("Invalid wish list keys")
        packed_franchise_wish_list = mkeys.pack()

        # Update Teams table
        update_stmt = text("""
            UPDATE `Teams`
            SET `franchiseWishList` = :franchiseWishList
            WHERE `teamID` = :teamID
        """)
        db.execute(update_stmt, {"franchiseWishList": packed_franchise_wish_list, "teamID": team_id})
        db.commit()

        return {
            "success": True,
            "teamID": team_id,
            "franchiseWishList": packed_franchise_wish_list
        }


class TeamsWishListSetAction:
    """Set team's wish list."""

    @staticmethod
    def execute(db: Session, team_id: int, user_id: int, wish_list_keys_str: str) -> dict:
        """Set team's wish list (pure data, no wrapper)."""
        # Query team to verify it exists and get owner
        team_stmt = text("""
            SELECT `userID`
            FROM `Teams`
            WHERE `teamID` = :teamID
            LIMIT 1
        """)
        team_result = db.execute(team_stmt, {"teamID": team_id})
        team_row = team_result.mappings().first()

        if not team_row:
            raise Exception(f"Team {team_id} not found")

        team_user_id = team_row["userID"]
        if team_user_id != user_id:
            raise Exception("Unauthorized: You do not own this team")

        # Parse wish list keys - handle both dot and comma separated formats
        if "." in wish_list_keys_str and "," not in wish_list_keys_str:
            wish_keys = [k.strip() for k in wish_list_keys_str.split(".") if k.strip()]
        else:
            wish_keys = [k.strip() for k in wish_list_keys_str.split(",") if k.strip()]

        # Build MKeys with list and pack
        mkeys = MKeys.build([wish_keys], size=1)
        if not mkeys:
            raise Exception("Invalid wish list keys")
        packed_wish_list = mkeys.pack()

        # Update Teams table
        update_stmt = text("""
            UPDATE `Teams`
            SET `membersWishList` = :membersWishList
            WHERE `teamID` = :teamID
        """)
        db.execute(update_stmt, {"membersWishList": packed_wish_list, "teamID": team_id})
        db.commit()

        return {
            "success": True,
            "teamID": team_id,
            "membersWishList": packed_wish_list
        }


class TeamsSetRealMembersRankingAction:
    """Set real members ranking for a team."""

    @staticmethod
    def execute(db: Session, team_id: int, user_id: int, member_keys_str: str) -> dict:
        """Set team's member ranking (pure data, no wrapper)."""
        # Query team to verify it exists and get owner
        team_stmt = text("""
            SELECT `userID`
            FROM `Teams`
            WHERE `teamID` = :teamID
            LIMIT 1
        """)
        team_result = db.execute(team_stmt, {"teamID": team_id})
        team_row = team_result.mappings().first()

        if not team_row:
            raise Exception(f"Team {team_id} not found")

        team_user_id = team_row["userID"]
        if team_user_id != user_id:
            raise Exception("Unauthorized: You do not own this team")

        # Parse member keys from comma-separated string
        member_keys = [k.strip() for k in member_keys_str.split(",") if k.strip()]

        # Build MKeys with list and pack
        mkeys = MKeys.build([member_keys], size=1)
        if not mkeys:
            raise Exception("Invalid member keys")
        packed_ranking = mkeys.pack()

        # Update Teams table
        update_stmt = text("""
            UPDATE `Teams`
            SET `membersRanking` = :membersRanking
            WHERE `teamID` = :teamID
        """)
        db.execute(update_stmt, {"membersRanking": packed_ranking, "teamID": team_id})
        db.commit()

        return {
            "success": True,
            "teamID": team_id,
            "membersRanking": packed_ranking
        }


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
        ranking_keys = MKeys.build(members_ranking_str, size=1)
        if not ranking_keys:
            return []

        keys = ranking_keys.get_group(0)

        # Create dict with ranking keys mapped to None initially
        my_dict = dict.fromkeys(keys, None)

        # Create MKeys for team and division membership
        team_mkeys = MKeys.build(team_members_str, size=1)
        division_mkeys = MKeys.build(team_members_div, size=1) if team_members_div else MKeys.build(None, size=1)

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
            team_group = team_mkeys.get_group(0) if team_mkeys else []
            division_group = division_mkeys.get_group(0) if division_mkeys else []
            member_dict["inTeam"] = 1 if member_key in team_group else 0
            member_dict["inDivision"] = 1 if member_key in division_group else 0
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


class TeamsWaiverMembersDetailAction:
    """Get waiver members detail for a team."""

    @staticmethod
    def execute(db: Session, team_id: int) -> list[dict]:
        """Get team's waiver members with their stats and waiver actions (pure data, no wrapper)."""
        # Query team to get membersWaivers and matchDayMapKey
        team_stmt = text("""
            SELECT `membersWaivers`, `matchDayMapKey`, `baseRealCompetitionID`
            FROM `Teams`
            WHERE `teamID` = :teamID
            LIMIT 1
        """)
        team_result = db.execute(team_stmt, {"teamID": team_id})
        team_row = team_result.mappings().first()

        if not team_row:
            return []

        members_waivers_str = team_row.get("membersWaivers") or ""
        match_day_map_key = team_row.get("matchDayMapKey")

        if not members_waivers_str or not match_day_map_key:
            return []

        # Query MatchDaysStatus to get realCompetitionID and realCompetitionMatchDay
        mds_stmt = text("""
            SELECT `realCompetitionID`, `realCompetitionMatchDay`
            FROM `MatchDaysStatus`
            WHERE `matchDayMapKey` = :matchDayMapKey
              AND `startWaivers` <= :currentDateTime
              AND `finishPostMatch` > :currentDateTime
            LIMIT 1
        """)
        mds_result = db.execute(mds_stmt, {
            "matchDayMapKey": match_day_map_key,
            "currentDateTime": RequestContext.get_datetime()
        })
        mds_row = mds_result.mappings().first()

        if not mds_row:
            return []

        real_competition_id = mds_row.get("realCompetitionID")
        real_competition_match_day = mds_row.get("realCompetitionMatchDay")

        # Parse members waivers using MKeys with allow_dups=True
        m_keys = MKeys.build(members_waivers_str, allow_dups=True)
        if not m_keys:
            return []

        members = []
        for g in range(m_keys.size):
            group_keys = m_keys.get_group(g)
            for k, key in enumerate(group_keys):
                # Query RealStandings for this member
                rs_stmt = text("""
                    SELECT *
                    FROM `RealStandings`
                    WHERE `realTeamMemberKey` = :key
                      AND `realCompetitionID` = :realCompetitionID
                      AND `realCompetitionMatchDay` = :realCompetitionMatchDay
                    LIMIT 1
                """)
                rs_result = db.execute(rs_stmt, {
                    "key": key,
                    "realCompetitionID": real_competition_id,
                    "realCompetitionMatchDay": real_competition_match_day
                })
                rs_row = rs_result.mappings().first()

                if rs_row:
                    member_dict = dict(rs_row)
                    member_dict["waiversGroup"] = g + 1
                    member_dict["waiversAction"] = "add" if k == 0 else "drop"
                    members.append(member_dict)

        return members
