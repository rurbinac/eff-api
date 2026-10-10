from sqlalchemy.orm import Session

from app.models import RealMatch, RealMatchTeam
from app.utils.dt import to_iso


class RealMatchesReadListAction:
    """Handle RealMatches ReadList requests."""

    @staticmethod
    def execute(
        db: Session,
        real_competition_id: int,
        real_competition_match_day: int | None = None,
    ) -> list[dict]:
        query = (
            db.query(RealMatch, RealMatchTeam)
            .join(RealMatchTeam, RealMatchTeam.realMatchID == RealMatch.realMatchID)
            .filter(RealMatch.realCompetitionID == real_competition_id)
            .filter(RealMatchTeam.realTeamNumber.in_([1, 2]))
        )
        if real_competition_match_day is not None:
            query = query.filter(RealMatch.realCompetitionMatchDay == real_competition_match_day)
        rows = query.order_by(
            RealMatch.realMatchDate.asc(),
            RealMatch.realMatchID.asc(),
            RealMatchTeam.realTeamNumber.asc(),
        ).all()
        items: list[dict] = []
        match_id = None
        prev_match = None
        match_teams = [None, None]
        for match, rmt in rows:
            if match_id is None:
                match_id = match.realMatchID
                prev_match = match
            elif match.realMatchID != match_id:
                RealMatchesReadListAction._serialize_match(items, prev_match, match_teams)
                match_id = match.realMatchID
                prev_match = match
                match_teams = [None, None]
            match_teams[rmt.realTeamNumber - 1] = rmt
        if prev_match is not None:
            RealMatchesReadListAction._serialize_match(items, prev_match, match_teams)
        return items

    @staticmethod
    def _serialize_match(items: list, match: RealMatch, rmt: list[RealMatchTeam]) -> None:
        rmt1 = rmt[0] if len(rmt) > 0 else None
        rmt2 = rmt[1] if len(rmt) > 1 else None

        items.append({
            "realMatchID": match.realMatchID,
            "realMatchStatus": match.realMatchStatus,
            "realMatchType": match.realMatchType,
            "realMatchPeriod": match.realMatchPeriod,
            "realMatchRealPeriod": match.realMatchRealPeriod,
            "realMatchAttendance": match.realMatchAttendance,
            "realMatchDate": to_iso(match.realMatchDate),
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
            "firstRealTeamMemberID": rmt1.realTeamMemberID if rmt1 else None,
            "firstRealTeamMemberKey": rmt1.realTeamMemberKey if rmt1 else None,
            "firstRealTeamID": rmt1.realTeamID if rmt1 else None,
            "firstRealTeamUID": rmt1.realTeamUID if rmt1 else None,
            "firstRealTeamName": rmt1.realTeamName if rmt1 else None,
            "firstRealTeamShortName": rmt1.realTeamShortName if rmt1 else None,
            "firstRealTeamScore": rmt1.realTeamScore if rmt1 else None,
            "firstRealTeamRealScore": rmt1.realTeamRealScore if rmt1 else None,
            "firstRealTeamSide": rmt1.realTeamSide if rmt1 else None,
            "firstRealTeamCleanSheet": rmt1.realTeamCleanSheet if rmt1 else None,
            "firstRealTeamResult": rmt1.realTeamResult if rmt1 else None,
            "firstRealTeamPoints": rmt1.realTeamPoints if rmt1 else None,
            "firstRealTeamNumber": rmt1.realTeamNumber if rmt1 else None,
            "secondRealTeamMemberID": rmt2.realTeamMemberID if rmt2 else None,
            "secondRealTeamMemberKey": rmt2.realTeamMemberKey if rmt2 else None,
            "secondRealTeamID": rmt2.realTeamID if rmt2 else None,
            "secondRealTeamUID": rmt2.realTeamUID if rmt2 else None,
            "secondRealTeamName": rmt2.realTeamName if rmt2 else None,
            "secondRealTeamShortName": rmt2.realTeamShortName if rmt2 else None,
            "secondRealTeamScore": rmt2.realTeamScore if rmt2 else None,
            "secondRealTeamRealScore": rmt2.realTeamRealScore if rmt2 else None,
            "secondRealTeamSide": rmt2.realTeamSide if rmt2 else None,
            "secondRealTeamCleanSheet": rmt2.realTeamCleanSheet if rmt2 else None,
            "secondRealTeamResult": rmt2.realTeamResult if rmt2 else None,
            "secondRealTeamPoints": rmt2.realTeamPoints if rmt2 else None,
            "secondRealTeamNumber": rmt2.realTeamNumber if rmt2 else None,
            "enabled": match.enabled,
            "lastF7Date": to_iso(match.lastF7Date),
            "lastF42Date": to_iso(match.lastF42Date),
            "lastFDate": to_iso(match.lastFDate),
            "createdIn": to_iso(match.createdIn),
            "updatedIn": to_iso(match.updatedIn),
        })
