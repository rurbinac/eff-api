import re

from sqlalchemy import bindparam, text
from sqlalchemy.orm import Session

from app.context import RequestContext
from app.guards import (
    require_division_member,
    require_league_member,
    require_team_owner,
)
from app.models import Team
from app.utils.dt import to_iso, utc_now
from app.utils.member_keys import KeyGroups, Keys


class TeamsReadListAction:
    """Get teams for a league or division."""

    @staticmethod
    def execute(
        db: Session,
        user_id: int,
        league_id: int | None = None,
        division_id: int | None = None,
    ) -> list[dict]:
        """Get teams filtered by league ID or division ID (pure data, no wrapper)."""
        query = db.query(Team)

        if league_id is not None:
            require_league_member(db, user_id, league_id=league_id)
            query = query.filter(Team.leagueID == league_id)
        elif division_id is not None:
            require_division_member(db, user_id, division_id=division_id)
            query = query.filter(Team.divisionID == division_id)
        else:
            return []

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
                "createdIn": to_iso(team.createdIn),
                "updatedBy": team.updatedBy,
                "updatedIn": to_iso(team.updatedIn),
            }
            items.append(row)

        # Return pure data (no response wrapper)
        return items


def _normalize_mkeys_str(raw: str | None) -> str:
    """Convert legacy concatenated-key format to MKeys dot-separated format.

    Legacy stored keys without separators (e.g. 'P123P456T7'), while MKeys
    expects 'P123.P456.T7.'. Strings already in MKeys format pass through.
    """
    if not raw:
        return ""
    s = raw.strip()
    if not s:
        return ""
    if s.endswith("."):
        return s
    keys = re.findall(r"[PT]\d+", s)
    return "".join(f"{k}." for k in keys)


class TeamsGetCurrentMembersAction:
    """Get current team members with real stats in roster order."""

    @staticmethod
    def execute(db: Session, team_id: int, user_id: int) -> list[dict]:
        """Get team members ordered by teamMembers field (pure data, no wrapper)."""
        require_league_member(db, user_id, team_id=team_id)
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

        keys = Keys.to_list(team_members_str)
        if not keys:
            return []

        # Create dict with keys in order, initialized to None
        my_dict = dict.fromkeys(keys, None)

        # Query real team members — use expanding bindparam so the list is
        # unpacked into individual placeholders: IN (:keys_0, :keys_1, ...)
        members_stmt = text("""
            SELECT *
            FROM `RealTeamMembers`
            WHERE `baseRealCompetitionID` = :baseRealCompetitionID
              AND `realTeamMemberKey` IN :keys
        """).bindparams(bindparam("keys", expanding=True))
        members_result = db.execute(
            members_stmt, {"baseRealCompetitionID": base_competition_id, "keys": keys}
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


class TeamsWishListDetailAction:
    """Get wish list members detail for a team."""

    @staticmethod
    def execute(db: Session, team_id: int, user_id: int) -> list[dict]:
        """Get team's wish list members with their stats, in wish-list order."""
        require_league_member(db, user_id, team_id=team_id)
        team_stmt = text("""
            SELECT `membersWishList`, `baseRealCompetitionID`
            FROM `Teams`
            WHERE `teamID` = :teamID
            LIMIT 1
        """)
        team_row = db.execute(team_stmt, {"teamID": team_id}).mappings().first()

        if not team_row:
            return []

        wish_list_str = team_row.get("membersWishList") or ""
        base_competition_id = team_row.get("baseRealCompetitionID")

        if not wish_list_str or not base_competition_id:
            return []

        keys = Keys.to_list(wish_list_str)
        if not keys:
            return []

        # Preserve wish-list order
        my_dict = dict.fromkeys(keys, None)

        members_stmt = text("""
            SELECT *
            FROM `RealTeamMembers`
            WHERE `baseRealCompetitionID` = :baseRealCompetitionID
              AND `realTeamMemberKey` IN :keys
        """).bindparams(bindparam("keys", expanding=True))
        members_result = db.execute(
            members_stmt,
            {"baseRealCompetitionID": base_competition_id, "keys": keys},
        )

        for row in members_result.mappings():
            member_dict = dict(row)
            key = member_dict.get("realTeamMemberKey")
            if key in my_dict:
                my_dict[key] = member_dict

        return [v for v in my_dict.values() if v is not None]


class TeamsSetFranchiseWishListAction:
    """Set team's franchise wish list."""

    @staticmethod
    def execute(
        db: Session, team_id: int, user_id: int, franchise_wish_list_keys_str: str
    ) -> dict:
        """Set team's franchise wish list (pure data, no wrapper)."""
        require_team_owner(db, user_id, team_id)

        # Parse franchise wish list keys - handle both dot and comma separated formats
        if (
            "." in franchise_wish_list_keys_str
            and "," not in franchise_wish_list_keys_str
        ):
            wish_keys = [
                k.strip() for k in franchise_wish_list_keys_str.split(".") if k.strip()
            ]
        else:
            wish_keys = [
                k.strip() for k in franchise_wish_list_keys_str.split(",") if k.strip()
            ]

        keys = Keys(wish_keys)
        if not keys:
            raise Exception("Invalid wish list keys")
        packed_franchise_wish_list = keys.to_str()

        # Update Teams table
        update_stmt = text("""
            UPDATE `Teams`
            SET `franchiseWishList` = :franchiseWishList
            WHERE `teamID` = :teamID
        """)
        db.execute(
            update_stmt,
            {"franchiseWishList": packed_franchise_wish_list, "teamID": team_id},
        )
        db.commit()

        return {
            "success": True,
            "teamID": team_id,
            "franchiseWishList": packed_franchise_wish_list,
        }


class TeamsWishListSetAction:
    """Set team's wish list."""

    @staticmethod
    def execute(
        db: Session, team_id: int, user_id: int, wish_list_keys_str: str
    ) -> dict:
        """Set team's wish list (pure data, no wrapper)."""
        require_team_owner(db, user_id, team_id)

        # Parse wish list keys - handle both dot and comma separated formats
        if "." in wish_list_keys_str and "," not in wish_list_keys_str:
            wish_keys = [k.strip() for k in wish_list_keys_str.split(".") if k.strip()]
        else:
            wish_keys = [k.strip() for k in wish_list_keys_str.split(",") if k.strip()]

        keys = Keys(wish_keys)
        if not keys:
            raise Exception("Invalid wish list keys")
        packed_wish_list = keys.to_str()

        # Update Teams table
        update_stmt = text("""
            UPDATE `Teams`
            SET `membersWishList` = :membersWishList
            WHERE `teamID` = :teamID
        """)
        db.execute(
            update_stmt, {"membersWishList": packed_wish_list, "teamID": team_id}
        )
        db.commit()

        return {"success": True, "teamID": team_id, "membersWishList": packed_wish_list}


class TeamsSetRealMembersRankingAction:
    """Set real members ranking for a team."""

    @staticmethod
    def execute(db: Session, team_id: int, user_id: int, member_keys_str: str) -> dict:
        """Set team's member ranking (pure data, no wrapper)."""
        require_team_owner(db, user_id, team_id)

        member_keys = [k.strip() for k in member_keys_str.split(",") if k.strip()]

        keys = Keys(member_keys)
        if not keys:
            raise Exception("Invalid member keys")
        packed_ranking = keys.to_str()

        # Update Teams table
        update_stmt = text("""
            UPDATE `Teams`
            SET `membersRanking` = :membersRanking
            WHERE `teamID` = :teamID
        """)
        db.execute(update_stmt, {"membersRanking": packed_ranking, "teamID": team_id})
        db.commit()

        return {"success": True, "teamID": team_id, "membersRanking": packed_ranking}


class TeamsGetRealMembersRankingAction:
    """Get real members ranking for a team."""

    @staticmethod
    def execute(db: Session, team_id: int, user_id: int) -> list[dict]:
        """Get real members with ranking metadata (pure data, no wrapper)."""
        require_league_member(db, user_id, team_id=team_id)
        require_league_member(db, user_id, team_id=team_id)
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
        members_ranking_str = _normalize_mkeys_str(target_team["membersRanking"])
        team_members_str = target_team["teamMembers"] or ""

        team_set: set[str] = set(Keys.to_list(team_members_str) or [])

        # Collect division member keys from all other teams in the same division
        division_teams_stmt = text("""
            SELECT `teamMembers`
            FROM `Teams`
            WHERE `divisionID` = :divisionID
              AND `teamID` != :teamID
        """)
        division_teams_result = db.execute(
            division_teams_stmt, {"divisionID": division_id, "teamID": team_id}
        )
        division_set: set[str] = set()
        for div_row in division_teams_result.mappings():
            div_keys = Keys.to_list(_normalize_mkeys_str(div_row.get("teamMembers")))
            if div_keys:
                division_set.update(div_keys)

        ranking_order: list[str] = Keys.to_list(members_ranking_str) or []
        ranking_set: set[str] = set(ranking_order)

        # Load all enabled members for this competition into an in-memory dict
        members_stmt = text("""
            SELECT *
            FROM `RealTeamMembers`
            WHERE `enabled` = 1
              AND `baseRealCompetitionID` = :baseRealCompetitionID
            ORDER BY IFNULL(`last_ranking`, 1000000000), `name`
        """)
        members_result = db.execute(
            members_stmt, {"baseRealCompetitionID": base_competition_id}
        )

        all_members: dict[str, dict] = {}
        for row in members_result.mappings():
            member_dict = dict(row)
            member_key = member_dict.get("realTeamMemberKey")
            if member_key is None:
                continue
            member_dict["inTeam"] = 1 if member_key in team_set else 0
            member_dict["inDivision"] = 1 if member_key in division_set else 0
            member_dict["inRanking"] = 1 if member_key in ranking_set else 0
            all_members[member_key] = member_dict

        # Ranked members first (preserving ranking order), then unranked remainder
        result: list[dict] = []
        for key in ranking_order:
            if key in all_members:
                result.append(all_members[key])
        for key, member in all_members.items():
            if key not in ranking_set:
                result.append(member)

        return result


class TeamsUpdateAction:
    """Update editable team settings (team owner only)."""

    @staticmethod
    def execute(
        db: Session,
        team_id: int,
        user_id: int,
        team_name: str | None = None,
        notes: str | None = None,
    ) -> dict:
        require_team_owner(db, user_id, team_id)
        team = db.get(Team, team_id)

        if team_name is not None:
            team.teamName = team_name
        if notes is not None:
            team.notes = notes

        team.updatedBy = user_id
        team.updatedIn = utc_now()
        db.commit()
        db.refresh(team)

        return {
            "teamID": team.teamID,
            "teamName": team.teamName,
            "notes": team.notes,
            "updatedBy": team.updatedBy,
            "updatedIn": to_iso(team.updatedIn),
        }


class TeamsWaiverMembersDetailAction:
    """Get waiver members detail for a team."""

    @staticmethod
    def execute(db: Session, team_id: int, user_id: int) -> list[dict]:
        """Get team's waiver members with their stats and waiver actions (pure data, no wrapper)."""
        require_league_member(db, user_id, team_id=team_id)
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
        mds_result = db.execute(
            mds_stmt,
            {
                "matchDayMapKey": match_day_map_key,
                "currentDateTime": RequestContext.get_datetime(),
            },
        )
        mds_row = mds_result.mappings().first()

        if not mds_row:
            return []

        real_competition_id = mds_row.get("realCompetitionID")
        real_competition_match_day = mds_row.get("realCompetitionMatchDay")

        kg = KeyGroups.unpack(members_waivers_str)
        if not kg:
            return []

        members = []
        for g, group in enumerate(kg):
            for k, key in enumerate(group):
                # Query RealStandings for this member
                rs_stmt = text("""
                    SELECT *
                    FROM `RealStandings`
                    WHERE `realTeamMemberKey` = :key
                      AND `realCompetitionID` = :realCompetitionID
                      AND `realCompetitionMatchDay` = :realCompetitionMatchDay
                    LIMIT 1
                """)
                rs_result = db.execute(
                    rs_stmt,
                    {
                        "key": key,
                        "realCompetitionID": real_competition_id,
                        "realCompetitionMatchDay": real_competition_match_day,
                    },
                )
                rs_row = rs_result.mappings().first()

                if rs_row:
                    member_dict = dict(rs_row)
                    member_dict["waiversGroup"] = g + 1
                    member_dict["waiversAction"] = "add" if k == 0 else "drop"
                    members.append(member_dict)

        return members
