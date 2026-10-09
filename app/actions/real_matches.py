from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models import RealMatchTeam
from app.utils.dt import to_iso


class RealMatchesReadListAction:
    """Handle RealMatches ReadList requests."""

    @staticmethod
    def execute(
        db: Session,
        real_competition_id: int,
        real_competition_match_day: int | None = None,
    ) -> list[dict]:
        where = ["realCompetitionID = :realCompetitionID"]
        params: dict = {"realCompetitionID": real_competition_id}

        if real_competition_match_day is not None:
            where.append("realCompetitionMatchDay = :realCompetitionMatchDay")
            params["realCompetitionMatchDay"] = real_competition_match_day

        sql = text(f"""
            SELECT realMatchID, realMatchStatus, realMatchType, realMatchPeriod,
                   realMatchRealPeriod, realMatchAttendance, realMatchDate,
                   realMatchDateOffset, realMatchResultType, realMatchTime,
                   realMatchFirstHalfTime, realMatchSecondHalfTime,
                   realMatchFirstHalfExtraTime, realMatchSecondHalfExtraTime,
                   realMatchEnded, realMatchIgnore,
                   realCompetitionID, realCompetitionUID, realCompetitionSYMID,
                   realCompetitionSeasonId, realCompetitionMatchDay,
                   realCompetitionFirstMatchDay, realCompetitionLastMatchDay,
                   baseRealCompetitionID, extraRealCompetitionID,
                   realVenueID, realVenueUID,
                   enabled, lastF7Date, lastF42Date, lastFDate,
                   createdIn, updatedIn
            FROM RealMatches
            WHERE {' AND '.join(where)}
            ORDER BY realMatchDate ASC, realMatchID ASC
        """)
        match_rows = [dict(r) for r in db.execute(sql, params).mappings()]

        if not match_rows:
            return []

        match_ids = [m["realMatchID"] for m in match_rows]
        team_rows: list[RealMatchTeam] = (
            db.query(RealMatchTeam)
            .filter(RealMatchTeam.realMatchID.in_(match_ids))
            .order_by(RealMatchTeam.realTeamNumber.asc())
            .all()
        )

        # Index teams by matchID
        teams_by_match: dict[int, dict[int, RealMatchTeam]] = {}
        for rmt in team_rows:
            teams_by_match.setdefault(rmt.realMatchID, {})[rmt.realTeamNumber] = rmt

        items: list[dict] = []
        for match in match_rows:
            teams = teams_by_match.get(match["realMatchID"], {})
            RealMatchesReadListAction._serialize_match(items, match, list(teams.values()))

        return items

    @staticmethod
    def _serialize_match(items: list, match: dict, rmt: list[RealMatchTeam]) -> None:
        rmt1 = None
        rmt2 = None
        for x in rmt:
            if x.realTeamNumber == 1:
                rmt1 = x
            elif x.realTeamNumber == 2:
                rmt2 = x

        items.append({
            "realMatchID": match["realMatchID"],
            "realMatchStatus": match["realMatchStatus"],
            "realMatchType": match["realMatchType"],
            "realMatchPeriod": match["realMatchPeriod"],
            "realMatchRealPeriod": match["realMatchRealPeriod"],
            "realMatchAttendance": match["realMatchAttendance"],
            "realMatchDate": to_iso(match["realMatchDate"]),
            "realMatchDateOffset": match["realMatchDateOffset"],
            "realMatchResultType": match["realMatchResultType"],
            "realMatchTime": match["realMatchTime"],
            "realMatchFirstHalfTime": match["realMatchFirstHalfTime"],
            "realMatchSecondHalfTime": match["realMatchSecondHalfTime"],
            "realMatchFirstHalfExtraTime": match["realMatchFirstHalfExtraTime"],
            "realMatchSecondHalfExtraTime": match["realMatchSecondHalfExtraTime"],
            "realMatchEnded": match["realMatchEnded"],
            "realMatchIgnore": match["realMatchIgnore"],
            "realCompetitionID": match["realCompetitionID"],
            "realCompetitionUID": match["realCompetitionUID"],
            "realCompetitionSYMID": match["realCompetitionSYMID"],
            "realCompetitionSeasonId": match["realCompetitionSeasonId"],
            "realCompetitionMatchDay": match["realCompetitionMatchDay"],
            "realCompetitionFirstMatchDay": match["realCompetitionFirstMatchDay"],
            "realCompetitionLastMatchDay": match["realCompetitionLastMatchDay"],
            "baseRealCompetitionID": match["baseRealCompetitionID"],
            "extraRealCompetitionID": match["extraRealCompetitionID"],
            "realVenueID": match["realVenueID"],
            "realVenueUID": match["realVenueUID"],
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
            "enabled": match["enabled"],
            "lastF7Date": to_iso(match["lastF7Date"]),
            "lastF42Date": to_iso(match["lastF42Date"]),
            "lastFDate": to_iso(match["lastFDate"]),
            "createdIn": to_iso(match["createdIn"]),
            "updatedIn": to_iso(match["updatedIn"]),
        })
