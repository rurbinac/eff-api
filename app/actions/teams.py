from sqlalchemy import bindparam, text
from sqlalchemy.orm import Session

from app.context import RequestContext
from app.guards import (
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
        if league_id is not None:
            require_league_member(db, user_id, league_id=league_id)
        elif division_id is not None:
            require_league_member(db, user_id, division_id=division_id)
        else:
            return []

        query = db.query(Team)

        if league_id is not None:
            query = query.filter(Team.leagueID == league_id)
        elif division_id is not None:
            query = query.filter(Team.divisionID == division_id)

        return [
            {
                "teamID": t.teamID,
                "baseRealCompetitionID": t.baseRealCompetitionID,
                "extraRealCompetitionID": t.extraRealCompetitionID,
                "matchDayMapKey": t.matchDayMapKey,
                "leagueID": t.leagueID,
                "divisionID": t.divisionID,
                "commissionerID": t.commissionerID,
                "userID": t.userID,
                "prevLeagueID": t.prevLeagueID,
                "nextLeagueID": t.nextLeagueID,
                "prevDivisionID": t.prevDivisionID,
                "nextDivisionID": t.nextDivisionID,
                "prevTeamID": t.prevTeamID,
                "nextTeamID": t.nextTeamID,
                "season": t.season,
                "seasonNum": t.seasonNum,
                "leagueMatches": t.leagueMatches,
                "divisionMatches": t.divisionMatches,
                "draftOrder": t.draftOrder,
                "randomOrder": t.randomOrder,
                "waiversOrder": t.waiversOrder,
                "teamName": t.teamName,
                "teamAvatar": t.teamAvatar,
                "teamMembers": t.teamMembers,
                "draftMembers": t.draftMembers,
                "membersRanking": t.membersRanking,
                "membersWaivers": t.membersWaivers,
                "membersWishList": t.membersWishList,
                "franchiseWishList": t.franchiseWishList,
                "fantasyPoints": t.fantasyPoints,
                "teamRanking": t.teamRanking,
                "locked": t.locked,
                "isCommissioner": t.isCommissioner,
                "cntEPLTeam": t.cntEPLTeam,
                "cntPlayer": t.cntPlayer,
                "cntGoalkeeper": t.cntGoalkeeper,
                "cntDefender": t.cntDefender,
                "cntMidfielder": t.cntMidfielder,
                "cntStriker": t.cntStriker,
                "cntAdd": t.cntAdd,
                "cntDrop": t.cntDrop,
                "cntWaiver": t.cntWaiver,
                "notes": t.notes,
                "place": t.place,
                "points": t.points,
                "statusC1": t.statusC1,
                "statusC2": t.statusC2,
                "statusC3": t.statusC3,
                "seedingC1": t.seedingC1,
                "seedingC2": t.seedingC2,
                "seedingC3": t.seedingC3,
                "createdBy": t.createdBy,
                "createdIn": to_iso(t.createdIn),
                "updatedBy": t.updatedBy,
                "updatedIn": to_iso(t.updatedIn),
            }
            for t in query.all()
        ]


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


class TeamsGetRealMembersRankingAction:
    """Get real members ranking for a team."""

    @staticmethod
    def execute(db: Session, team_id: int, user_id: int) -> list[dict]:
        """Get real members with ranking metadata (pure data, no wrapper)."""
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
        team_set: set[str] = set(Keys.to_list(target_team["teamMembers"]) or [])

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
            div_keys = Keys.to_list(div_row.get("teamMembers"))
            if div_keys:
                division_set.update(div_keys)

        ranking_order: list[str] = Keys.to_list(target_team["membersRanking"]) or []
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


class TeamsSetRealMembersRankingAction:
    """Set real members ranking for a team."""

    @staticmethod
    def execute(db: Session, team_id: int, user_id: int, member_keys_str: str) -> dict:
        """Set team's member ranking (pure data, no wrapper)."""
        require_team_owner(db, user_id, team_id)
        return _set_member_keys_field(db, team_id, "membersRanking", member_keys_str)


class TeamsWishListDetailAction:
    """Get wish list members detail for a team."""

    @staticmethod
    def execute(db: Session, team_id: int, user_id: int) -> list[dict]:
        """Get team's wish list members with their stats, in wish-list order."""
        require_league_member(db, user_id, team_id=team_id)
        return _get_member_keys_field(db, team_id, "membersWishList")


class TeamsWishListSetAction:
    """Set team's wish list."""

    @staticmethod
    def execute(
        db: Session, team_id: int, user_id: int, wish_list_keys_str: str
    ) -> dict:
        """Set team's wish list (pure data, no wrapper)."""
        require_team_owner(db, user_id, team_id)
        return _set_member_keys_field(
            db, team_id, "membersWishList", wish_list_keys_str
        )


class TeamsFranchiseWishListDetailAction:
    """Get franchise wish list members detail for a team."""

    @staticmethod
    def execute(db: Session, team_id: int, user_id: int) -> list[dict]:
        """Get team's franchise wish list members with their stats, in wish-list order."""
        require_league_member(db, user_id, team_id=team_id)
        return _get_member_keys_field(db, team_id, "franchiseWishList")


class TeamsSetFranchiseWishListAction:
    """Set team's franchise wish list."""

    @staticmethod
    def execute(
        db: Session, team_id: int, user_id: int, franchise_wish_list_keys_str: str
    ) -> dict:
        """Set team's franchise wish list (pure data, no wrapper)."""
        require_team_owner(db, user_id, team_id)
        return _set_member_keys_field(
            db, team_id, "franchiseWishList", franchise_wish_list_keys_str
        )


def _get_member_keys_field(db: Session, team_id: int, field: str) -> list[dict]:
    team_row = (
        db.execute(
            text(
                f"SELECT `{field}`, `baseRealCompetitionID` FROM `Teams` WHERE `teamID` = :teamID LIMIT 1"
            ),
            {"teamID": team_id},
        )
        .mappings()
        .first()
    )
    if not team_row:
        return []
    keys = Keys.to_list(team_row.get(field) or "")
    base_competition_id = team_row.get("baseRealCompetitionID")
    if not keys or not base_competition_id:
        return []
    my_dict = dict.fromkeys(keys, None)
    members_result = db.execute(
        text("""
            SELECT *
            FROM `RealTeamMembers`
            WHERE `baseRealCompetitionID` = :baseRealCompetitionID
              AND `realTeamMemberKey` IN :keys
        """).bindparams(bindparam("keys", expanding=True)),
        {"baseRealCompetitionID": base_competition_id, "keys": keys},
    )
    for row in members_result.mappings():
        member_dict = dict(row)
        key = member_dict.get("realTeamMemberKey")
        if key in my_dict:
            my_dict[key] = member_dict
    return [v for v in my_dict.values() if v is not None]


def _set_member_keys_field(
    db: Session, team_id: int, field: str, keys_str: str
) -> dict:
    key_list = Keys.to_list(keys_str)
    if not key_list:
        raise Exception(f"Invalid keys for {field}")
    packed = Keys(key_list).to_str()
    db.execute(
        text(f"UPDATE `Teams` SET `{field}` = :value WHERE `teamID` = :teamID"),
        {"value": packed, "teamID": team_id},
    )
    db.commit()
    return {"success": True, "teamID": team_id, field: packed}
