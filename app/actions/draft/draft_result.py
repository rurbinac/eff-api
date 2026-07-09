from sqlalchemy.orm import Session
from sqlalchemy import text


class DraftResultAction:

    @staticmethod
    def execute(db: Session, division_id: int) -> list[dict]:
        stmt = text("""
            SELECT teamID, baseRealCompetitionID, leagueID, divisionID, commissionerID,
                   userID, seasonNum, draftOrder, randomOrder, teamName, isCommissioner,
                   cntEPLTeam, cntPlayer, cntGoalkeeper, cntDefender, cntMidfielder,
                   cntStriker, teamMembers, draftMembers
            FROM Teams
            WHERE divisionID = :divisionID
            ORDER BY draftOrder ASC
        """)
        team_rows = [dict(r) for r in db.execute(stmt, {"divisionID": division_id}).mappings()]

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
    placeholders = ", ".join(f":key{i}" for i in range(len(keys)))
    params = {f"key{i}": key for i, key in enumerate(keys)}
    stmt = text(f"""
        SELECT realTeamMemberKey, realTeamID, realTeamUID, realTeamName, realTeamShortName,
               realPlayerID, realPlayerUID, firstName, lastName, knownName, name,
               draftPosition, draftPositionOrder
        FROM RealTeamMembers
        WHERE realTeamMemberKey IN ({placeholders})
    """)
    return [dict(r) for r in db.execute(stmt, params).mappings()]
