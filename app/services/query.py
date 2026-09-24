from datetime import datetime
from typing import Any, ClassVar

from sqlalchemy.orm import Session
from sqlmodel import SQLModel

from app.constants import MatchDayStatusConstants, RealCompetitionConstants
from app.context import RequestContext
from app.models import (
    Division,
    DivisionNotes,
    League,
    Lookup,
    MatchDaysStatus,
    RealCompetition,
    RealStanding,
    Team,
    User,
)
from app.utils.dt import to_iso


class QueryService:
    """Service class for common database queries."""

    # Cache for get_current_base_competition, keyed by season_id.
    # Invalidate with clear_real_competition_cache() after updating RealCompetitions.
    _real_competition_cache: ClassVar[dict[int, dict | None]] = {}

    @classmethod
    def clear_real_competition_cache(cls) -> None:
        """Invalidate the cached result of get_current_base_competition."""
        cls._real_competition_cache.clear()

    @staticmethod
    def get_season_id(dt: datetime | None = None, delta_seasons: int = 0) -> int:
        """
        Calculate current season ID based on month.
        If current month is 1-7 (Jan-Jul), season = previous year
        If current month is 8-12 (Aug-Dec), season = current year
        """
        if dt is None:
            dt = RequestContext.get_datetime()

        if dt.month >= RealCompetitionConstants.SEASON_START_MONTH:
            return dt.year + delta_seasons
        else:
            return dt.year - 1 + delta_seasons

    @staticmethod
    def get_competition(db: Session, id: int | None = None) -> dict | None:
        """Get a RealCompetition by its ID."""
        if id is None:
            return QueryService.get_current_base_competition(db)
        for rc in QueryService._real_competition_cache.values():
            if rc and rc.get("realCompetitionID") == id:
                return rc

        return QueryService._return_competition(
            db.query(RealCompetition)
            .filter(RealCompetition.realCompetitionID == id)
            .first()
        )

    @staticmethod
    def get_base_competition(db: Session, id: int | None = None) -> dict | None:
        """Get the base RealCompetition for the given competition ID."""
        rc = QueryService.get_competition(db, id)
        if not rc:
            return None
        if rc["realCompetitionID"] == rc["baseRealCompetitionID"]:
            return rc
        return QueryService.get_competition(db, rc["baseRealCompetitionID"])

    @staticmethod
    def get_extra_competition(db: Session, id: int | None = None) -> dict | None:
        """Get the extra RealCompetition for the given competition ID."""
        rc = QueryService.get_competition(db, id)
        if not rc:
            return None
        if rc["realCompetitionID"] == rc["extraRealCompetitionID"]:
            return rc
        return QueryService.get_competition(db, rc["extraRealCompetitionID"])

    @staticmethod
    def get_current_base_competition(
        db: Session, delta_seasons: int = 0
    ) -> dict | None:
        """Get the current base RealCompetition (EN_PR).

        Results are cached in-process per season_id. Call
        QueryService.clear_real_competition_cache() after updating RealCompetitions.
        """
        return QueryService._get_current_competition(
            db, RealCompetitionConstants.BASE_SYMID, delta_seasons=delta_seasons
        )

    @staticmethod
    def get_current_extra_competition(
        db: Session, delta_seasons: int = 0
    ) -> dict | None:
        """Get the current extra RealCompetition (EN_PR_CUP).

        Results are cached in-process per season_id. Call
        QueryService.clear_real_competition_cache() after updating RealCompetitions.
        """
        return QueryService._get_current_competition(
            db, RealCompetitionConstants.EXTRA_SYMID, delta_seasons=delta_seasons
        )

    @staticmethod
    def get_competition_id(db: Session, id: int | None = None) -> int | None:
        rc = QueryService.get_competition(db, id)
        return rc["realCompetitionID"] if rc else None

    @staticmethod
    def get_base_competition_id(db: Session, id: int | None = None) -> int | None:
        rc = QueryService.get_base_competition(db, id)
        return rc["realCompetitionID"] if rc else None

    @staticmethod
    def get_extra_competition_id(db: Session, id: int | None = None) -> int | None:
        rc = QueryService.get_extra_competition(db, id)
        return rc["realCompetitionID"] if rc else None


    @staticmethod
    def _get_current_competition(
        db: Session, symid: str, delta_seasons: int = 0
    ) -> dict | None:
        """Get the current RealCompetition for the given SYMID and season.

        Results are cached in-process per season_id. Call
        QueryService.clear_real_competition_cache() after updating RealCompetitions.
        """
        season_id = QueryService.get_season_id(delta_seasons=delta_seasons)
        for rc in QueryService._real_competition_cache.values():
            if (
                rc
                and rc.get("realCompetitionSYMID") == symid
                and rc.get("realCompetitionSeasonId") == str(season_id)
            ):
                return rc

        return QueryService._return_competition(
            db.query(RealCompetition)
            .filter(
                RealCompetition.realCompetitionSYMID == symid,
                RealCompetition.realCompetitionSeasonId == str(season_id),
            )
            .first()
        )

    @staticmethod
    def _return_competition(rc) -> dict | None:
        if not rc:
            return None
        rc_dict = QueryService._to_dict(rc)
        QueryService._real_competition_cache[rc.realCompetitionID] = rc_dict
        return rc_dict

    @staticmethod
    def get_current_match_day_status(
        db: Session,
        base_real_competition_id: int | None = None,
        match_day_map_key: str | None = None,
        current_datetime: datetime | None = None,
        include_boundaries: bool = False,
    ) -> dict | None:
        """Get current MatchDayStatus for the base competition, determining which phase we're in."""
        if not isinstance(current_datetime, datetime):
            current_datetime = RequestContext.get_datetime()

        if match_day_map_key is None:
            if base_real_competition_id is None:
                brc = QueryService.get_current_base_competition(db)
                if isinstance(brc, dict):
                    base_real_competition_id = brc["baseRealCompetitionID"]
                else:
                    return None
            match_day_map_key = str(base_real_competition_id)
        # Find a MatchDaysStatus record that spans the current time
        mds = (
            db.query(MatchDaysStatus)
            .filter(
                MatchDaysStatus.matchDayMapKey == match_day_map_key,
                MatchDaysStatus.startWaivers <= current_datetime,
                MatchDaysStatus.finishPostMatch > current_datetime,
            )
            .first()
        )

        if not mds:
            return None

        return QueryService._mds_to_dict(mds, current_datetime, include_boundaries)

    @staticmethod
    def get_match_day_status(
        db: Session,
        real_competition_id: int,
        real_competition_match_day: int,
        match_day_map_key: str,
    ) -> dict | None:
        mds = (
            db.query(MatchDaysStatus)
            .filter(
                MatchDaysStatus.realCompetitionID == real_competition_id,
                MatchDaysStatus.realCompetitionMatchDay == real_competition_match_day,
                MatchDaysStatus.matchDayMapKey == match_day_map_key,
            )
            .first()
        )
        if not mds:
            return None
        return QueryService._mds_to_dict(mds, include_boundaries=True)

    @staticmethod
    def _mds_to_dict(
        mds: MatchDaysStatus,
        current_datetime: datetime | None = None,
        include_boundaries: bool = False,
    ) -> dict:
        if not isinstance(current_datetime, datetime):
            current_datetime = RequestContext.get_datetime()
        head = {"baseRealCompetitionMatchDay": mds.realCompetitionMatchDay}
        include = [
            "realCompetitionID",
            "realCompetitionMatchDay",
            "realCompetitionMatchDaySort",
            "prevActiveRealCompetitionID",
            "prevActiveRealCompetitionMatchDay",
            "nextActiveRealCompetitionID",
            "nextActiveRealCompetitionMatchDay",
            "finishBaseMatchDay",
        ]
        tail = {
            "matchDayStatus": None,
            "matchDayStatusStart": None,
            "matchDayStatusFinish": None,
        }
        for phase, (start, finish) in MatchDayStatusConstants.boundaries():
            if not tail["matchDayStatus"]:
                finish_field = getattr(mds, finish, None)
                if finish_field and current_datetime < finish_field:
                    tail["matchDayStatus"] = phase
                    start_field = getattr(mds, start, None)
                    tail["matchDayStatusStart"] = to_iso(start_field)
                    tail["matchDayStatusFinish"] = to_iso(finish_field)
            if include_boundaries:
                include.append(start)
                include.append(finish)
        if not include_boundaries:
            include.append("startPreMatch")
            include.append("startPostMatch")
        return QueryService._to_dict(mds, include=include, head=head, tail=tail)

    @staticmethod
    def _to_dict(
        obj: SQLModel,
        exclude: list[str] | None = None,
        include: list[str] | None = None,
        head: dict[str, Any] | None = None,
        tail: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Convert SQLAlchemy model instance to dictionary."""
        if head is None:
            head = {}
        if tail is None:
            tail = {}
        if include is None:
            include = []
        if exclude is None:
            exclude = []

        result = head.copy()

        if isinstance(obj, SQLModel):
            all_columns = obj.__table__.columns.keys()
            columns_to_use = include if include else all_columns

            for column in columns_to_use:
                # Check if column exists and is not excluded
                if column in all_columns and column not in exclude:
                    result[column] = getattr(obj, column)

        return result | tail.copy()

    @staticmethod
    def get_show_data(db: Session) -> dict | None:
        """Get current show data (what to display)."""
        current_datetime = RequestContext.get_datetime()

        sd = (
            db.query(MatchDaysStatus)
            .filter(MatchDaysStatus.finishBaseMatchDay <= current_datetime)
            .order_by(MatchDaysStatus.finishBaseMatchDay.desc())
            .first()
        )

        if not sd:
            return None

        return {
            "showRealCompetitionID": sd.realCompetitionID,
            "showRealCompetitionMatchDay": sd.realCompetitionMatchDay,
        }

    @staticmethod
    def get_top_epl_teams(db: Session, limit: int = 4) -> list[str]:
        """Get top EPL teams by standings position."""
        season_id = QueryService.get_season_id()

        teams = (
            db.query(RealStanding.realTeamShortName)
            .join(
                RealCompetition,
                (RealCompetition.realCompetitionID == RealStanding.realCompetitionID)
                & (
                    RealCompetition.realCompetitionLastMatchDay
                    == RealStanding.realCompetitionMatchDay
                ),
            )
            .filter(
                RealStanding.isTeam == 1,
                RealCompetition.realCompetitionSYMID
                == RealCompetitionConstants.BASE_SYMID,
                RealCompetition.realCompetitionSeasonId == str(season_id),
            )
            .order_by(RealStanding.place.asc())
            .limit(limit)
            .all()
        )

        return [team[0] for team in teams]

    @staticmethod
    def get_leagues_by_user(db: Session, user_id: int) -> list[dict]:
        """Get all leagues where user has a team, with division and team info."""
        current_datetime = RequestContext.get_datetime()

        query = (
            db.query(
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
                League.lowestEPLTeam,
                League.lowestGoalkeeper,
                League.lowestDefender,
                League.lowestMidfielder,
                League.lowestStriker,
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
                User.userName.label("commissionerUserName"),
                User.firstName.label("commissionerFirstName"),
                User.lastName.label("commissionerLastName"),
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
            )
            .join(Division, Division.leagueID == League.leagueID)
            .join(Team, Team.divisionID == Division.divisionID)
            .join(User, User.userID == League.commissionerID)
            .outerjoin(
                MatchDaysStatus,
                (MatchDaysStatus.matchDayMapKey == Division.matchDayMapKey)
                & (MatchDaysStatus.startWaivers <= current_datetime)
                & (MatchDaysStatus.finishPostMatch > current_datetime),
            )
            .filter(Team.userID == user_id)
            .order_by(League.leagueName)
        )

        return [
            {
                "leagueID": r.leagueID,
                "baseRealCompetitionID": r.baseRealCompetitionID,
                "extraRealCompetitionID": r.extraRealCompetitionID,
                "leagueName": r.leagueName,
                "commissionerID": r.commissionerID,
                "prevLeagueID": r.prevLeagueID,
                "nextLeagueID": r.nextLeagueID,
                "season": r.season,
                "seasonNum": r.seasonNum,
                "numDivisions": r.numDivisions,
                "leagueType": r.leagueType,
                "gameType": r.gameType,
                "scoringSystem": r.scoringSystem,
                "tradeDeadline": to_iso(r.tradeDeadline),
                "publishLeague": r.publishLeague,
                "seasonStatus": r.seasonStatus,
                "totalTeams": r.totalTeams,
                "availableTeams": r.availableTeams,
                "totPromoted": r.totPromoted,
                "maxFranchiseMembers": r.maxFranchiseMembers,
                "maxWaiver": r.maxWaiver,
                "minEPLTeam": r.minEPLTeam,
                "minPlayer": r.minPlayer,
                "minGoalkeeper": r.minGoalkeeper,
                "minDefender": r.minDefender,
                "minMidfielder": r.minMidfielder,
                "minStriker": r.minStriker,
                "maxEPLTeam": r.maxEPLTeam,
                "maxPlayer": r.maxPlayer,
                "maxGoalkeeper": r.maxGoalkeeper,
                "maxDefender": r.maxDefender,
                "maxMidfielder": r.maxMidfielder,
                "maxStriker": r.maxStriker,
                "lowestEPLTeam": r.lowestEPLTeam,
                "lowestGoalkeeper": r.lowestGoalkeeper,
                "lowestDefender": r.lowestDefender,
                "lowestMidfielder": r.lowestMidfielder,
                "lowestStriker": r.lowestStriker,
                "createdBy": r.createdBy,
                "createdIn": to_iso(r.createdIn),
                "updatedBy": r.updatedBy,
                "updatedIn": to_iso(r.updatedIn),
                "divisionID": r.divisionID,
                "matchDayMapKey": r.matchDayMapKey,
                "divisionType": r.divisionType,
                "draftType": r.draftType,
                "draftDate": to_iso(r.draftDate),
                "draftStatus": r.draftStatus,
                "draftingStart": to_iso(r.draftingStart),
                "draftingFinish": to_iso(r.draftingFinish),
                "draftingRound": r.draftingRound,
                "draftingTeamOrder": r.draftingTeamOrder,
                "matchDay": r.matchDay,
                "isCupMatchDay": r.isCupMatchDay,
                "isDivisionCupMatchDay": r.isDivisionCupMatchDay,
                "numTeams": r.numTeams,
                "firstRealCompetitionMatchDay": r.firstRealCompetitionMatchDay,
                "lastRealCompetitionMatchDay": r.lastRealCompetitionMatchDay,
                "teamID": r.teamID,
                "userID": r.userID,
                "draftOrder": r.draftOrder,
                "teamName": r.teamName,
                "teamAvatar": r.teamAvatar,
                "fantasyPoints": r.fantasyPoints,
                "teamRanking": r.teamRanking,
                "locked": r.locked,
                "isCommissioner": r.isCommissioner,
                "cntPlayer": r.cntPlayer,
                "cntGoalkeeper": r.cntGoalkeeper,
                "cntDefender": r.cntDefender,
                "cntMidfielder": r.cntMidfielder,
                "cntStriker": r.cntStriker,
                "cntAdd": r.cntAdd,
                "cntDrop": r.cntDrop,
                "cntWaiver": r.cntWaiver,
                "place": r.place,
                "points": r.points,
                "statusC1": r.statusC1,
                "statusC2": r.statusC2,
                "statusC3": r.statusC3,
                "commissionerUserName": r.commissionerUserName,
                "commissionerFirstName": r.commissionerFirstName,
                "commissionerLastName": r.commissionerLastName,
                "scriptsStatus": r.scriptsStatus,
                "startMatchDay": to_iso(r.startMatchDay),
                "finishMatchDay": to_iso(r.finishMatchDay),
                "startWaivers": to_iso(r.startWaivers),
                "finishWaivers": to_iso(r.finishWaivers),
                "startWaiversSettle": to_iso(r.startWaiversSettle),
                "finishWaiversSettle": to_iso(r.finishWaiversSettle),
                "startOpenWaivers": to_iso(r.startOpenWaivers),
                "finishOpenWaivers": to_iso(r.finishOpenWaivers),
                "startOpenWaiversSettle": to_iso(r.startOpenWaiversSettle),
                "finishOpenWaiversSettle": to_iso(r.finishOpenWaiversSettle),
                "startPreMatch": to_iso(r.startPreMatch),
                "finishPreMatch": to_iso(r.finishPreMatch),
                "startMatch": to_iso(r.startMatch),
                "finishMatch": to_iso(r.finishMatch),
                "startPostMatch": to_iso(r.startPostMatch),
                "finishPostMatch": to_iso(r.finishPostMatch),
            }
            for r in query.all()
        ]

    @staticmethod
    def get_divisions_by_league(db: Session, league_id: int) -> list[dict]:
        """Get all divisions for a league."""
        return [
            {
                "divisionID": d.divisionID,
                "baseRealCompetitionID": d.baseRealCompetitionID,
                "extraRealCompetitionID": d.extraRealCompetitionID,
                "matchDayMapKey": d.matchDayMapKey,
                "leagueID": d.leagueID,
                "commissionerID": d.commissionerID,
                "prevLeagueID": d.prevLeagueID,
                "nextLeagueID": d.nextLeagueID,
                "prevDivisionID": d.prevDivisionID,
                "nextDivisionID": d.nextDivisionID,
                "season": d.season,
                "seasonNum": d.seasonNum,
                "leagueMatches": d.leagueMatches,
                "divisionMatches": d.divisionMatches,
                "draftType": d.draftType,
                "draftDate": to_iso(d.draftDate),
                "draftCompleteDate": to_iso(d.draftCompleteDate),
                "draftStatus": d.draftStatus,
                "draftTime": d.draftTime,
                "draftingStart": to_iso(d.draftingStart),
                "draftingFinish": to_iso(d.draftingFinish),
                "draftingLimit": to_iso(d.draftingLimit),
                "draftingRound": d.draftingRound,
                "draftingMemberOrder": d.draftingMemberOrder,
                "draftingTeamOrder": d.draftingTeamOrder,
                "draftingNextTeamOrder": d.draftingNextTeamOrder,
                "draftingUsers": d.draftingUsers,
                "draftingHooks": d.draftingHooks,
                "franchiseMembers": d.franchiseMembers,
                "firstRealCompetitionMatchDay": d.firstRealCompetitionMatchDay,
                "lastRealCompetitionMatchDay": d.lastRealCompetitionMatchDay,
                "waiverStatus": d.waiverStatus,
                "matchDay": d.matchDay,
                "isCupMatchDay": d.isCupMatchDay,
                "isDivisionCupMatchDay": d.isDivisionCupMatchDay,
                "totalTeams": d.totalTeams,
                "numTeams": d.numTeams,
                "availableTeams": d.availableTeams,
                "divisionType": d.divisionType,
                "createdBy": d.createdBy,
                "createdIn": to_iso(d.createdIn),
                "updatedBy": d.updatedBy,
                "updatedIn": to_iso(d.updatedIn),
            }
            for d in db.query(Division).filter(Division.leagueID == league_id).order_by(Division.divisionID).all()
        ]

    @staticmethod
    def get_teams_by_league(db: Session, league_id: int) -> list[dict]:
        """Get all teams for a league."""
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
            for t in db.query(Team).filter(Team.leagueID == league_id).order_by(Team.teamID).all()
        ]

    @staticmethod
    def get_division_notes(db: Session, division_id: int) -> list[dict]:
        """Get all notes for a division."""
        query = (
            db.query(DivisionNotes)
            .filter(DivisionNotes.divisionID == division_id)
            .order_by(DivisionNotes.divisionNoteID)
        )

        return [
            {
                "divisionNoteID": n.divisionNoteID,
                "leagueID": n.leagueID,
                "divisionID": n.divisionID,
                "teamID": n.teamID,
                "userID": n.userID,
                "commissionerID": n.commissionerID,
                "parentDivisionNoteID": n.parentDivisionNoteID,
                "userName": n.userName,
                "title": n.title,
                "notes": n.notes,
                "divisionNoteType": n.divisionNoteType,
                "createdBy": n.createdBy,
                "createdIn": to_iso(n.createdIn),
                "updatedBy": n.updatedBy,
                "updatedIn": to_iso(n.updatedIn),
            }
            for n in query.all()
        ]

    @staticmethod
    def validate_lookup(db: Session, lookup_num: int, lookup_key: str | int) -> bool:
        """
        Validate a value against the Lookups table.

        Args:
            db: Database session
            lookup_num: The lookup number (category)
            lookup_key: The value to validate (stored in lookupKey field)

        Returns:
            True if the lookup exists, False otherwise
        """
        return (
            db.query(Lookup)
            .filter(Lookup.lookupNum == lookup_num, Lookup.lookupKey == str(lookup_key))
            .first()
        ) is not None

    @staticmethod
    def get_lookups_by_num(db: Session, lookup_num: int) -> list[dict]:
        """
        Get all lookups for a given lookupNum, ordered by position.

        Args:
            db: Database session
            lookup_num: The lookup number (category)

        Returns:
            List of dicts with lookupKey and lookupText, ordered by position
        """
        query = (
            db.query(Lookup)
            .filter(Lookup.lookupNum == lookup_num)
            .order_by(Lookup.position)
        )

        return [
            {
                "lookupKey": lookup.lookupKey,
                "lookupText": lookup.lookupText,
                "position": lookup.position,
            }
            for lookup in query.all()
        ]

    @staticmethod
    def get_real_standings_by_match_day(
        db: Session,
        real_competition_id: int,
        real_competition_match_day: int,
        real_team_member_key: str,
    ) -> dict | None:
        """
        Get real standings for a given competition and match day, filtered by team member key.

        Args:
            db: Database session
            real_competition_id: The ID of the real competition
            real_competition_match_day: The match day number
            real_team_member_key: The team member key to filter by
        """
        result = (
            db.query(RealStanding)
            .filter(
                RealStanding.realCompetitionID == real_competition_id,
                RealStanding.realCompetitionMatchDay == real_competition_match_day,
                RealStanding.realTeamMemberKey == real_team_member_key,
            )
            .first()
        )
        if result is None:
            return None
        include = [
            "realTeamMemberKey",
            "realTeamMemberID",
            "realMatchID",
            "realMatchStatus",
            "realTeamID",
            "realTeamUID",
            "realTeamName",
            "realTeamShortName",
            "realTeamSide",
            "oppositeRealTeamID",
            "oppositeRealTeamUID",
            "oppositeRealTeamName",
            "oppositeRealTeamShortName",
            "realPlayerID",
            "realPlayerUID",
            "firstName",
            "lastName",
            "knownName",
            "name",
            "sortName",
            "draftPosition",
            "draftPositionOrder",
            "timePlayed",
            "gamePlayed",
            "goals",
            "assists",
            "yellowCards",
            "redCards",
            "goalsConceded",
            "cleanSheet",
            "matchDayPlayed",
            "played",
            "won",
            "draw",
            "lost",
            "goalsFor",
            "goalsAgainst",
            "matchPointsL1",
            "pointsL1",
            "livePointsL1",
            "matchTeamMemberRole",
            "matchTeamMemberPlayed",
            "matchTeamID",
            "teamID",
            "matchStatus",
        ]
        return QueryService._to_dict(result, include=include)
