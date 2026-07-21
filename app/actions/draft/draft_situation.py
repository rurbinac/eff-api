from sqlalchemy.orm import Session

from app.actions.draft.draft_notice import DraftNotice
from app.actions.draft.draft_values import DraftValues


class DraftSituationAction:
    @staticmethod
    def execute(db: Session, division_id: int) -> dict | None:
        dv = DraftValues(db, division_id)
        dv.load_division()

        if dv.division is None:
            return None

        dv.load_teams()

        d = dv.division
        drafting_users = ",".join(str(u) for u in dv.get_drafting_users())

        teams = []
        commissioners = []
        team_members = []
        for team in dv.teams:
            teams.append(team["teamID"])
            if team["isCommissioner"]:
                commissioners.append(team["teamID"])
            raw = team.get("teamMembers") or ""
            team_members.append(raw[:-1].split() if raw else [])

        return {
            "divisionID": d["divisionID"],
            "draftTime": d["draftTime"],
            "draftStatus": d["draftStatus"],
            "draftingStart": d.get("draftingStart"),
            "draftingFinish": d.get("draftingFinish"),
            "draftingLimit": d.get("draftingLimit"),
            "draftingRound": d.get("draftingRound"),
            "draftingMemberOrder": d.get("draftingMemberOrder"),
            "draftingTeamOrder": d.get("draftingTeamOrder"),
            "draftingNextTeamOrder": d.get("draftingNextTeamOrder"),
            "draftingUsers": drafting_users,
            "draftChannel": DraftNotice.division_channel(division_id),
            "teams": ",".join(str(t) for t in teams),
            "commissioners": ",".join(str(c) for c in commissioners),
            "teamMembers": ",".join(_team_members_sequence(team_members)),
        }


def _team_members_sequence(team_members: list[list[str]]) -> list[str]:
    if not team_members:
        return []

    result = []
    i = 0
    delta = 1

    team_members_copy = [list(members) for members in team_members]

    while team_members_copy[i]:
        result.append(team_members_copy[i].pop(0))
        i += delta

        if i < 0 or i >= len(team_members_copy):
            i -= delta
            delta = -delta

    return result
