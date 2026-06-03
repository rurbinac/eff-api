from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models import RealCompetition, MatchDaysStatus, League, Division, Team, User, DivisionNotes
from app.context import RequestContext


class QueryService:
    """Service class for common database queries."""

    SEASON_START_MONTH = 8
    BASE_SYMID = 'EN_PR'
    EXTRA_SYMID = 'EN_FA'

    @staticmethod
    def get_season_id(dt: datetime | None = None) -> int:
        """
        Calculate current season ID based on month.
        If current month is 1-7 (Jan-Jul), season = current year
        If current month is 8-12 (Aug-Dec), season = current year - 1
        """
        if dt is None:
            dt = RequestContext.get_datetime()

        if dt.month < QueryService.SEASON_START_MONTH:
            return dt.year
        else:
            return dt.year - 1

    @staticmethod
    def get_current_base_competition(db: Session) -> dict | None:
        """Get the current base RealCompetition (EN_PR)."""
        season_id = QueryService.get_season_id()
        rc = db.query(RealCompetition).filter(
            RealCompetition.realCompetitionSYMID == QueryService.BASE_SYMID,
            RealCompetition.realCompetitionSeasonId == str(season_id)
        ).first()

        if not rc:
            return None

        return {
            "baseRealCompetitionID": rc.realCompetitionID,
            "realCompetitionLastMatchDay": rc.realCompetitionLastMatchDay,
            "extraRealCompetitionID": rc.extraRealCompetitionID,
            "baseRealCompetitionMatchDayBeforeExtra": rc.realCompetitionExtraMatchDay,
            "useExtraRealCompetition": rc.useExtraRealCompetition,
        }

    @staticmethod
    def get_current_match_day_status(db: Session, base_real_competition_id: int) -> dict | None:
        """Get current MatchDayStatus for the base competition."""
        current_datetime = RequestContext.get_datetime()

        mds = db.query(MatchDaysStatus).filter(
            MatchDaysStatus.matchDayMapKey == str(base_real_competition_id),
            MatchDaysStatus.startWaivers <= current_datetime,
            MatchDaysStatus.finishPostMatch > current_datetime
        ).first()

        if not mds:
            return None

        return {
            "realCompetitionID": mds.realCompetitionID,
            "realCompetitionMatchDay": mds.realCompetitionMatchDay,
            "baseRealCompetitionMatchDay": mds.realCompetitionMatchDay,
            "matchDayStatus": mds.scriptsStatus,
            "matchDayStatusStart": mds.startMatchDay.isoformat() if mds.startMatchDay else None,
            "matchDayStatusFinish": mds.finishMatchDay.isoformat() if mds.finishMatchDay else None,
            "realCompetitionMatchDaySort": mds.realCompetitionMatchDaySort,
            "prevActiveRealCompetitionID": mds.prevActiveRealCompetitionID,
            "prevActiveRealCompetitionMatchDay": mds.prevActiveRealCompetitionMatchDay,
            "nextActiveRealCompetitionID": mds.nextActiveRealCompetitionID,
            "nextActiveRealCompetitionMatchDay": mds.nextActiveRealCompetitionMatchDay,
        }

    @staticmethod
    def get_show_data(db: Session) -> dict | None:
        """Get current show data (what to display)."""
        current_datetime = RequestContext.get_datetime()

        sd = db.query(MatchDaysStatus).filter(
            MatchDaysStatus.finishBaseMatchDay <= current_datetime
        ).order_by(MatchDaysStatus.finishBaseMatchDay.desc()).first()

        if not sd:
            return None

        return {
            "showRealCompetitionID": sd.realCompetitionID,
            "showRealCompetitionMatchDay": sd.realCompetitionMatchDay,
        }

    @staticmethod
    def get_leagues_by_user(db: Session, user_id: int) -> list[dict]:
        """Get all leagues where user has a team, with division and team info."""
        current_datetime = RequestContext.get_datetime()

        query = db.query(
            League.leagueID,
            League.baseRealCompetitionID,
            League.extraRealCompetitionID,
            League.leagueName,
            League.commissionerID,
            League.prevLeagueID,
            League.nextLeagueID,
            League.season,
            League.seasonNum,
            League.numDivisions,
            League.leagueType,
            League.gameType,
            League.scoringSystem,
            League.tradeDeadline,
            League.publishLeague,
            League.seasonStatus,
            League.totalTeams,
            League.availableTeams,
            League.totPromoted,
            League.maxFranchiseMembers,
            League.maxWaiver,
            League.minEPLTeam,
            League.minPlayer,
            League.minGoalkeeper,
            League.minDefender,
            League.minMidfielder,
            League.minStriker,
            League.maxEPLTeam,
            League.maxPlayer,
            League.maxGoalkeeper,
            League.maxDefender,
            League.maxMidfielder,
            League.maxStriker,
            League.autoEPLTeam,
            League.autoGoalkeeper,
            League.autoDefender,
            League.autoMidfielder,
            League.autoStriker,
            League.createdBy,
            League.createdIn,
            League.updatedBy,
            League.updatedIn,
            Division.divisionID,
            Division.matchDayMapKey,
            Division.divisionType,
            Division.draftType,
            Division.draftDate,
            Division.draftStatus,
            Division.draftingStart,
            Division.draftingFinish,
            Division.draftingRound,
            Division.draftingTeamOrder,
            Division.matchDay,
            Division.isCupMatchDay,
            Division.isDivisionCupMatchDay,
            Division.numTeams,
            Division.firstRealCompetitionMatchDay,
            Division.lastRealCompetitionMatchDay,
            Team.teamID,
            Team.userID,
            Team.draftOrder,
            Team.teamName,
            Team.teamAvatar,
            Team.fantasyPoints,
            Team.teamRanking,
            Team.locked,
            Team.isCommissioner,
            Team.cntPlayer,
            Team.cntGoalkeeper,
            Team.cntDefender,
            Team.cntMidfielder,
            Team.cntStriker,
            Team.cntAdd,
            Team.cntDrop,
            Team.cntWaiver,
            Team.place,
            Team.points,
            Team.statusC1,
            Team.statusC2,
            Team.statusC3,
            User.userName.label('commissionerUserName'),
            User.firstName.label('commissionerFirstName'),
            User.lastName.label('commissionerLastName'),
            MatchDaysStatus.scriptsStatus,
            MatchDaysStatus.startMatchDay,
            MatchDaysStatus.finishMatchDay,
            MatchDaysStatus.startWaivers,
            MatchDaysStatus.finishWaivers,
            MatchDaysStatus.startWaiversSettle,
            MatchDaysStatus.finishWaiversSettle,
            MatchDaysStatus.startOpenWaivers,
            MatchDaysStatus.finishOpenWaivers,
            MatchDaysStatus.startOpenWaiversSettle,
            MatchDaysStatus.finishOpenWaiversSettle,
            MatchDaysStatus.startPreMatch,
            MatchDaysStatus.finishPreMatch,
            MatchDaysStatus.startMatch,
            MatchDaysStatus.finishMatch,
            MatchDaysStatus.startPostMatch,
            MatchDaysStatus.finishPostMatch,
        ).join(Division, Division.leagueID == League.leagueID) \
         .join(Team, Team.divisionID == Division.divisionID) \
         .join(User, User.userID == League.commissionerID) \
         .outerjoin(MatchDaysStatus,
            (MatchDaysStatus.matchDayMapKey == Division.matchDayMapKey) &
            (MatchDaysStatus.startWaivers <= current_datetime) &
            (MatchDaysStatus.finishPostMatch > current_datetime)
        ).filter(Team.userID == user_id) \
         .order_by(League.leagueName)

        results = []
        for row in query.all():
            row_dict = {
                'leagueID': row.leagueID,
                'baseRealCompetitionID': row.baseRealCompetitionID,
                'extraRealCompetitionID': row.extraRealCompetitionID,
                'leagueName': row.leagueName,
                'commissionerID': row.commissionerID,
                'prevLeagueID': row.prevLeagueID,
                'nextLeagueID': row.nextLeagueID,
                'season': row.season,
                'seasonNum': row.seasonNum,
                'numDivisions': row.numDivisions,
                'leagueType': row.leagueType,
                'gameType': row.gameType,
                'scoringSystem': row.scoringSystem,
                'tradeDeadline': row.tradeDeadline.isoformat() if row.tradeDeadline else None,
                'publishLeague': row.publishLeague,
                'seasonStatus': row.seasonStatus,
                'totalTeams': row.totalTeams,
                'availableTeams': row.availableTeams,
                'totPromoted': row.totPromoted,
                'maxFranchiseMembers': row.maxFranchiseMembers,
                'maxWaiver': row.maxWaiver,
                'minEPLTeam': row.minEPLTeam,
                'minPlayer': row.minPlayer,
                'minGoalkeeper': row.minGoalkeeper,
                'minDefender': row.minDefender,
                'minMidfielder': row.minMidfielder,
                'minStriker': row.minStriker,
                'maxEPLTeam': row.maxEPLTeam,
                'maxPlayer': row.maxPlayer,
                'maxGoalkeeper': row.maxGoalkeeper,
                'maxDefender': row.maxDefender,
                'maxMidfielder': row.maxMidfielder,
                'maxStriker': row.maxStriker,
                'autoEPLTeam': row.autoEPLTeam,
                'autoGoalkeeper': row.autoGoalkeeper,
                'autoDefender': row.autoDefender,
                'autoMidfielder': row.autoMidfielder,
                'autoStriker': row.autoStriker,
                'createdBy': row.createdBy,
                'createdIn': row.createdIn.isoformat() if row.createdIn else None,
                'updatedBy': row.updatedBy,
                'updatedIn': row.updatedIn.isoformat() if row.updatedIn else None,
                'divisionID': row.divisionID,
                'matchDayMapKey': row.matchDayMapKey,
                'divisionType': row.divisionType,
                'draftType': row.draftType,
                'draftDate': row.draftDate.isoformat() if row.draftDate else None,
                'draftStatus': row.draftStatus,
                'draftingStart': row.draftingStart.isoformat() if row.draftingStart else None,
                'draftingFinish': row.draftingFinish.isoformat() if row.draftingFinish else None,
                'draftingRound': row.draftingRound,
                'draftingTeamOrder': row.draftingTeamOrder,
                'matchDay': row.matchDay,
                'isCupMatchDay': row.isCupMatchDay,
                'isDivisionCupMatchDay': row.isDivisionCupMatchDay,
                'numTeams': row.numTeams,
                'firstRealCompetitionMatchDay': row.firstRealCompetitionMatchDay,
                'lastRealCompetitionMatchDay': row.lastRealCompetitionMatchDay,
                'teamID': row.teamID,
                'userID': row.userID,
                'draftOrder': row.draftOrder,
                'teamName': row.teamName,
                'teamAvatar': row.teamAvatar,
                'fantasyPoints': row.fantasyPoints,
                'teamRanking': row.teamRanking,
                'locked': row.locked,
                'isCommissioner': row.isCommissioner,
                'cntPlayer': row.cntPlayer,
                'cntGoalkeeper': row.cntGoalkeeper,
                'cntDefender': row.cntDefender,
                'cntMidfielder': row.cntMidfielder,
                'cntStriker': row.cntStriker,
                'cntAdd': row.cntAdd,
                'cntDrop': row.cntDrop,
                'cntWaiver': row.cntWaiver,
                'place': row.place,
                'points': row.points,
                'statusC1': row.statusC1,
                'statusC2': row.statusC2,
                'statusC3': row.statusC3,
                'commissionerUserName': row.commissionerUserName,
                'commissionerFirstName': row.commissionerFirstName,
                'commissionerLastName': row.commissionerLastName,
                'scriptsStatus': row.scriptsStatus,
                'startMatchDay': row.startMatchDay.isoformat() if row.startMatchDay else None,
                'finishMatchDay': row.finishMatchDay.isoformat() if row.finishMatchDay else None,
                'startWaivers': row.startWaivers.isoformat() if row.startWaivers else None,
                'finishWaivers': row.finishWaivers.isoformat() if row.finishWaivers else None,
                'startWaiversSettle': row.startWaiversSettle.isoformat() if row.startWaiversSettle else None,
                'finishWaiversSettle': row.finishWaiversSettle.isoformat() if row.finishWaiversSettle else None,
                'startOpenWaivers': row.startOpenWaivers.isoformat() if row.startOpenWaivers else None,
                'finishOpenWaivers': row.finishOpenWaivers.isoformat() if row.finishOpenWaivers else None,
                'startOpenWaiversSettle': row.startOpenWaiversSettle.isoformat() if row.startOpenWaiversSettle else None,
                'finishOpenWaiversSettle': row.finishOpenWaiversSettle.isoformat() if row.finishOpenWaiversSettle else None,
                'startPreMatch': row.startPreMatch.isoformat() if row.startPreMatch else None,
                'finishPreMatch': row.finishPreMatch.isoformat() if row.finishPreMatch else None,
                'startMatch': row.startMatch.isoformat() if row.startMatch else None,
                'finishMatch': row.finishMatch.isoformat() if row.finishMatch else None,
                'startPostMatch': row.startPostMatch.isoformat() if row.startPostMatch else None,
                'finishPostMatch': row.finishPostMatch.isoformat() if row.finishPostMatch else None,
            }
            results.append(row_dict)

        return results

    @staticmethod
    def get_divisions_by_league(db: Session, league_id: int) -> list[dict]:
        """Get all divisions for a league."""
        query = db.query(Division).filter(
            Division.leagueID == league_id
        ).order_by(Division.divisionID)

        results = []
        for division in query.all():
            row_dict = {
                'divisionID': division.divisionID,
                'baseRealCompetitionID': division.baseRealCompetitionID,
                'extraRealCompetitionID': division.extraRealCompetitionID,
                'matchDayMapKey': division.matchDayMapKey,
                'leagueID': division.leagueID,
                'commissionerID': division.commissionerID,
                'prevLeagueID': division.prevLeagueID,
                'nextLeagueID': division.nextLeagueID,
                'prevDivisionID': division.prevDivisionID,
                'nextDivisionID': division.nextDivisionID,
                'season': division.season,
                'seasonNum': division.seasonNum,
                'leagueMatches': division.leagueMatches,
                'divisionMatches': division.divisionMatches,
                'draftType': division.draftType,
                'draftDate': division.draftDate.isoformat() if division.draftDate else None,
                'draftCompleteDate': division.draftCompleteDate.isoformat() if division.draftCompleteDate else None,
                'draftStatus': division.draftStatus,
                'draftTime': division.draftTime,
                'draftingStart': division.draftingStart.isoformat() if division.draftingStart else None,
                'draftingFinish': division.draftingFinish.isoformat() if division.draftingFinish else None,
                'draftingLimit': division.draftingLimit.isoformat() if division.draftingLimit else None,
                'draftingRound': division.draftingRound,
                'draftingMemberOrder': division.draftingMemberOrder,
                'draftingTeamOrder': division.draftingTeamOrder,
                'draftingNextTeamOrder': division.draftingNextTeamOrder,
                'draftingUsers': division.draftingUsers,
                'draftingHooks': division.draftingHooks,
                'franchiseMembers': division.franchiseMembers,
                'firstRealCompetitionMatchDay': division.firstRealCompetitionMatchDay,
                'lastRealCompetitionMatchDay': division.lastRealCompetitionMatchDay,
                'waiverStatus': division.waiverStatus,
                'matchDay': division.matchDay,
                'isCupMatchDay': division.isCupMatchDay,
                'isDivisionCupMatchDay': division.isDivisionCupMatchDay,
                'totalTeams': division.totalTeams,
                'numTeams': division.numTeams,
                'availableTeams': division.availableTeams,
                'divisionType': division.divisionType,
                'createdBy': division.createdBy,
                'createdIn': division.createdIn.isoformat() if division.createdIn else None,
                'updatedBy': division.updatedBy,
                'updatedIn': division.updatedIn.isoformat() if division.updatedIn else None,
            }
            results.append(row_dict)

        return results

    @staticmethod
    def get_teams_by_league(db: Session, league_id: int) -> list[dict]:
        """Get all teams for a league."""
        query = db.query(Team).filter(
            Team.leagueID == league_id
        ).order_by(Team.teamID)

        results = []
        for team in query.all():
            row_dict = {
                'teamID': team.teamID,
                'baseRealCompetitionID': team.baseRealCompetitionID,
                'extraRealCompetitionID': team.extraRealCompetitionID,
                'matchDayMapKey': team.matchDayMapKey,
                'leagueID': team.leagueID,
                'divisionID': team.divisionID,
                'commissionerID': team.commissionerID,
                'userID': team.userID,
                'prevLeagueID': team.prevLeagueID,
                'nextLeagueID': team.nextLeagueID,
                'prevDivisionID': team.prevDivisionID,
                'nextDivisionID': team.nextDivisionID,
                'prevTeamID': team.prevTeamID,
                'nextTeamID': team.nextTeamID,
                'season': team.season,
                'seasonNum': team.seasonNum,
                'leagueMatches': team.leagueMatches,
                'divisionMatches': team.divisionMatches,
                'draftOrder': team.draftOrder,
                'randomOrder': team.randomOrder,
                'waiversOrder': team.waiversOrder,
                'teamName': team.teamName,
                'teamAvatar': team.teamAvatar,
                'teamMembers': team.teamMembers,
                'draftMembers': team.draftMembers,
                'membersRanking': team.membersRanking,
                'membersWaivers': team.membersWaivers,
                'membersWishList': team.membersWishList,
                'franchiseWishList': team.franchiseWishList,
                'fantasyPoints': team.fantasyPoints,
                'teamRanking': team.teamRanking,
                'locked': team.locked,
                'isCommissioner': team.isCommissioner,
                'cntEPLTeam': team.cntEPLTeam,
                'cntPlayer': team.cntPlayer,
                'cntGoalkeeper': team.cntGoalkeeper,
                'cntDefender': team.cntDefender,
                'cntMidfielder': team.cntMidfielder,
                'cntStriker': team.cntStriker,
                'cntAdd': team.cntAdd,
                'cntDrop': team.cntDrop,
                'cntWaiver': team.cntWaiver,
                'notes': team.notes,
                'place': team.place,
                'points': team.points,
                'statusC1': team.statusC1,
                'statusC2': team.statusC2,
                'statusC3': team.statusC3,
                'seedingC1': team.seedingC1,
                'seedingC2': team.seedingC2,
                'seedingC3': team.seedingC3,
                'createdBy': team.createdBy,
                'createdIn': team.createdIn.isoformat() if team.createdIn else None,
                'updatedBy': team.updatedBy,
                'updatedIn': team.updatedIn.isoformat() if team.updatedIn else None,
            }
            results.append(row_dict)

        return results

    @staticmethod
    def get_division_notes(db: Session, division_id: int) -> list[dict]:
        """Get all notes for a division."""
        try:
            query = db.query(DivisionNotes).filter(
                DivisionNotes.divisionID == division_id
            ).order_by(DivisionNotes.divisionNoteID)

            results = []
            for note in query.all():
                row_dict = {
                    'divisionNoteID': note.divisionNoteID,
                    'leagueID': note.leagueID,
                    'divisionID': note.divisionID,
                    'teamID': note.teamID,
                    'userID': note.userID,
                    'commissionerID': note.commissionerID,
                    'parentDivisionNoteID': note.parentDivisionNoteID,
                    'userName': note.userName,
                    'title': note.title,
                    'notes': note.notes,
                    'divisionNoteType': note.divisionNoteType,
                    'createdBy': note.createdBy,
                    'createdIn': note.createdIn.isoformat() if note.createdIn else None,
                    'updatedBy': note.updatedBy,
                    'updatedIn': note.updatedIn.isoformat() if note.updatedIn else None,
                }
                results.append(row_dict)

            return results
        except Exception:
            # Table may not exist yet - return empty list
            return []
