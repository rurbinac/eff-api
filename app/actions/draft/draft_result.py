from sqlalchemy import select
from sqlalchemy.orm import Session

from app.guards import require_league_member
from app.models import RealTeamMember, Team


class DraftResultAction:

    @staticmethod
    def execute(db: Session, division_id: int, user_id: int | None = None) -> list[dict]:
        require_league_member(db, user_id, division_id=division_id)
        stmt = (
            select(
                Team.teamID, Team.baseRealCompetitionID, Team.leagueID, Team.divisionID,
                Team.commissionerID, Team.userID, Team.seasonNum, Team.draftOrder,
                Team.randomOrder, Team.teamName, Team.isCommissioner, Team.cntEPLTeam,
                Team.cntPlayer, Team.cntGoalkeeper, Team.cntDefender, Team.cntMidfielder,
                Team.cntStriker, Team.teamMembers, Team.draftMembers,
            )
            .where(Team.divisionID == division_id)
            .order_by(Team.draftOrder)
        )
        team_rows = [dict(r) for r in db.execute(stmt).mappings()]

        members = _build_members(db, team_rows)
        members.sort(key=lambda m: m["draftingMemberOrder"])
        return members


def _build_members(db: Session, teams: list[dict]) -> list[dict]:
    num_teams = len(teams)
    members = []

    for team in teams:
        raw = team.get("teamMembers") or ""
        keys = [k for k in raw.rstrip(".").split(".") if k]

        team_data = {k: v for k, v in team.items() if k not in ("teamMembers", "draftMembers")}

        if not keys:
            continue

        member_map = {r["realTeamMemberKey"]: r for r in _get_member_details(db, keys)}

        for i, key in enumerate(keys):
            row = member_map.get(key)
            if not row:
                continue

            if i % 2 == 0:
                drafting_order = (i * num_teams) + team_data["draftOrder"]
            else:
                drafting_order = ((i + 1) * num_teams) - team_data["draftOrder"] + 1

            members.append({
                **team_data,
                **row,
                "draftingRound": i + 1,
                "draftingMemberOrder": drafting_order,
            })

    return members


def _get_member_details(db: Session, keys: list[str]) -> list[dict]:
    rows = db.scalars(
        select(RealTeamMember).where(RealTeamMember.realTeamMemberKey.in_(keys))
    ).all()
    fields = [
        "realTeamMemberKey", "realTeamID", "realTeamUID", "realTeamName", "realTeamShortName",
        "realPlayerID", "realPlayerUID", "firstName", "lastName", "knownName", "name",
        "draftPosition", "draftPositionOrder",
    ]
    return [{f: getattr(r, f) for f in fields} for r in rows]
