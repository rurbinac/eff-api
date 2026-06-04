from sqlalchemy.orm import Session
from app.models import Team
from app.context import RequestContext


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
