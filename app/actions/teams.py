from sqlalchemy import text
from sqlalchemy.orm import Session

from app.constants import WaiversConstants
from app.context import RequestContext
from app.exceptions import CannotSaveException, RequiredValueException
from app.guards import (
    require_division_commissioner,
    require_league_member,
    require_team,
    require_team_owner,
)
from app.models import Team
from app.services import QueryService
from app.utils.dt import to_iso, utc_now
from app.utils.readers import RTMReader
from app.utils.rtm_keys import KeyGroups, Keys, MemberKeys


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

        members_by_key = QueryService.get_real_team_members_by_keys(db, keys)
        return [members_by_key[k] for k in keys if k in members_by_key]


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

        kg = KeyGroups.to_list(members_waivers_str)
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


class TeamsWaiversRequestAction:
    """Set or deletes team's waivers request."""

    @staticmethod
    def execute(db: Session, team_id: int, user_id: int, keys: KeyGroups) -> dict:
        team = require_team_owner(db, user_id, team_id)
        team_members: set[str] = set(Keys.to_list(team.teamMembers or "") or [])
        for group in keys:
            if not group:
                continue
            add, *drops = group
            if add in team_members:
                raise RequiredValueException("membersWaivers", "WaiversRequest")
            for drop in drops:
                if drop not in team_members:
                    raise RequiredValueException("membersWaivers", "WaiversRequest")
        keys.compress()
        return _set_member_keys_field(db, team_id, "membersWaivers", keys)


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
    def execute(db: Session, team_id: int, user_id: int, keys: Keys) -> dict:
        """Set team's member ranking (pure data, no wrapper)."""
        require_team_owner(db, user_id, team_id)
        return _set_member_keys_field(db, team_id, "membersRanking", keys)


class TeamsAddAndDropMembersAction:
    """Toggle team members: keys already in teamMembers are dropped, others are added."""

    @staticmethod
    def execute(db: Session, team_id: int, user_id: int, keys: Keys) -> dict:
        team = require_team_owner(db, user_id, team_id)
        reader = RTMReader(db)
        member_keys = MemberKeys(reader)
        member_keys.unpack(team.teamMembers)

        to_add, to_drop = member_keys.get_add_drops(keys)

        if to_add:
            div_keys = TeamsAddAndDropMembersAction._read_division_keys(db, team)
            for key in to_add:
                if key in div_keys:
                    raise CannotSaveException("teamMembers", f"{key} is already taken in the division")

        if isinstance(WaiversConstants.MAX_ADD, int) and len(to_add) > WaiversConstants.MAX_ADD:
            raise CannotSaveException("teamMembers", f"too many adds (max {WaiversConstants.MAX_ADD})")
        if isinstance(WaiversConstants.MAX_DROP, int) and len(to_drop) > WaiversConstants.MAX_DROP:
            raise CannotSaveException("teamMembers", f"too many drops (max {WaiversConstants.MAX_DROP})")

        reader.load(keys=member_keys + to_add)

        if not member_keys.try_change(to_add, to_drop):
            raise CannotSaveException("teamMembers", "invalid team composition after changes")

        packed = member_keys.pack()
        team.teamMembers = packed
        team.cntAdd += len(to_add)
        team.cntDrop += len(to_drop)
        team.updatedBy = user_id
        team.updatedIn = utc_now()
        db.commit()
        return {"teamID": team.teamID, "teamMembers": packed}

    @staticmethod
    def _read_division_keys(db: Session, team: Team) -> Keys:
        rows = (
            db.execute(
                text(
                    "SELECT `teamMembers` FROM `Teams` WHERE `divisionID` = :div AND `teamID` != :tid"
                ),
                {"div": team.divisionID, "tid": team.teamID},
            )
            .mappings()
            .all()
        )
        division_keys = Keys(allow_dups=None)
        for row in rows:
            for key in Keys.to_list(row.get("teamMembers") or "") or []:
                division_keys.append(key)
        return division_keys


class TeamsMakeCommissionerAction:
    """Grant or revoke co-commissioner status on a team (division commissioner only)."""

    @staticmethod
    def execute(db: Session, team_id: int, user_id: int, make: bool) -> dict:
        team = require_team(db, team_id)
        require_division_commissioner(db, user_id, team_id=team_id)
        team.isCommissioner = 1 if make else 0
        team.updatedBy = user_id
        team.updatedIn = utc_now()
        db.commit()
        db.refresh(team)
        return {"teamID": team.teamID, "isCommissioner": team.isCommissioner}


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
    def execute(db: Session, team_id: int, user_id: int, keys: Keys) -> dict:
        """Set team's wish list (pure data, no wrapper)."""
        require_team_owner(db, user_id, team_id)
        return _set_member_keys_field(db, team_id, "membersWishList", keys)


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
    def execute(db: Session, team_id: int, user_id: int, keys: Keys) -> dict:
        """Set team's franchise wish list (pure data, no wrapper)."""
        require_team_owner(db, user_id, team_id)
        return _set_member_keys_field(db, team_id, "franchiseWishList", keys)


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
    members_by_key = QueryService.get_real_team_members_by_keys(db, keys)
    return [members_by_key[k] for k in keys if k in members_by_key]


def _set_member_keys_field(
    db: Session, team_id: int, field: str, keys: Keys | KeyGroups
) -> dict:
    packed = keys.pack()
    db.execute(
        text(f"UPDATE `Teams` SET `{field}` = :value WHERE `teamID` = :teamID"),
        {"value": packed, "teamID": team_id},
    )
    db.commit()
    return {"success": True, "teamID": team_id, field: packed}
