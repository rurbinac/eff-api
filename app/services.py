from datetime import datetime
from sqlalchemy.orm import Session

from app.models import RealCompetition, MatchDaysStatus
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
