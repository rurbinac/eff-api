from datetime import datetime
from sqlalchemy.orm import Session
from app.models import RealMatch
from app.context import RequestContext


class RealMatchesReadListAction:
    """Handle RealMatches ReadList requests."""

    @staticmethod
    def execute(
        db: Session,
        real_competition_id: int | None = None,
        real_competition_match_day: int | None = None,
    ) -> list[dict]:
        """
        Get real matches filtered by competition and match day.

        Args:
            db: Database session
            real_competition_id: Filter by realCompetitionID
            real_competition_match_day: Filter by realCompetitionMatchDay

        Returns:
            PHP-compatible response dict
        """
        query = db.query(RealMatch)

        if real_competition_id is not None:
            query = query.filter(RealMatch.realCompetitionID == real_competition_id)

        if real_competition_match_day is not None:
            query = query.filter(
                RealMatch.realCompetitionMatchDay == real_competition_match_day
            )

        matches = query.order_by(RealMatch.realMatchDate).all()

        items = []
        for match in matches:
            values = {
                "realMatchID": match.realMatchID,
                "realMatchStatus": match.realMatchStatus,
                "realMatchType": match.realMatchType,
                "realMatchPeriod": match.realMatchPeriod,
                "realMatchRealPeriod": match.realMatchRealPeriod,
                "realMatchAttendance": match.realMatchAttendance,
                "realMatchDate": match.realMatchDate.isoformat() if match.realMatchDate else None,
                "realMatchDateOffset": match.realMatchDateOffset,
                "realMatchResultType": match.realMatchResultType,
                "realMatchTime": match.realMatchTime,
                "realMatchFirstHalfTime": match.realMatchFirstHalfTime,
                "realMatchSecondHalfTime": match.realMatchSecondHalfTime,
                "realMatchFirstHalfExtraTime": match.realMatchFirstHalfExtraTime,
                "realMatchSecondHalfExtraTime": match.realMatchSecondHalfExtraTime,
                "realMatchEnded": match.realMatchEnded,
                "realMatchIgnore": match.realMatchIgnore,
                "realCompetitionID": match.realCompetitionID,
                "realCompetitionUID": match.realCompetitionUID,
                "realCompetitionSYMID": match.realCompetitionSYMID,
                "realCompetitionSeasonId": match.realCompetitionSeasonId,
                "realCompetitionMatchDay": match.realCompetitionMatchDay,
                "realCompetitionFirstMatchDay": match.realCompetitionFirstMatchDay,
                "realCompetitionLastMatchDay": match.realCompetitionLastMatchDay,
                "baseRealCompetitionID": match.baseRealCompetitionID,
                "extraRealCompetitionID": match.extraRealCompetitionID,
                "realVenueID": match.realVenueID,
                "realVenueUID": match.realVenueUID,
                "firstRealTeamMemberID": match.firstRealTeamMemberID,
                "firstRealTeamMemberKey": match.firstRealTeamMemberKey,
                "firstRealTeamID": match.firstRealTeamID,
                "firstRealTeamUID": match.firstRealTeamUID,
                "firstRealTeamName": match.firstRealTeamName,
                "firstRealTeamShortName": match.firstRealTeamShortName,
                "firstRealTeamScore": match.firstRealTeamScore,
                "firstRealTeamRealScore": match.firstRealTeamRealScore,
                "firstRealTeamSide": match.firstRealTeamSide,
                "firstRealTeamCleanSheet": match.firstRealTeamCleanSheet,
                "firstRealTeamResult": match.firstRealTeamResult,
                "firstRealTeamPoints": match.firstRealTeamPoints,
                "firstRealTeamNumber": match.firstRealTeamNumber,
                "secondRealTeamMemberID": match.secondRealTeamMemberID,
                "secondRealTeamMemberKey": match.secondRealTeamMemberKey,
                "secondRealTeamID": match.secondRealTeamID,
                "secondRealTeamUID": match.secondRealTeamUID,
                "secondRealTeamName": match.secondRealTeamName,
                "secondRealTeamShortName": match.secondRealTeamShortName,
                "secondRealTeamScore": match.secondRealTeamScore,
                "secondRealTeamRealScore": match.secondRealTeamRealScore,
                "secondRealTeamSide": match.secondRealTeamSide,
                "secondRealTeamCleanSheet": match.secondRealTeamCleanSheet,
                "secondRealTeamResult": match.secondRealTeamResult,
                "secondRealTeamPoints": match.secondRealTeamPoints,
                "secondRealTeamNumber": match.secondRealTeamNumber,
                "enabled": match.enabled,
                "lastF7Date": match.lastF7Date.isoformat() if match.lastF7Date else None,
                "lastF42Date": match.lastF42Date.isoformat() if match.lastF42Date else None,
                "lastFDate": match.lastFDate.isoformat() if match.lastFDate else None,
                "createdIn": match.createdIn.isoformat() if match.createdIn else None,
                "updatedIn": match.updatedIn.isoformat() if match.updatedIn else None,
            }
            items.append({"values": values})

        return {
            "table": "RealMatches",
            "timestamp": RequestContext.get_datetime().strftime("%Y-%m-%d %H:%M:%S"),
            "items": items,
        }
