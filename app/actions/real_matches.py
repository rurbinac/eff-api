from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models import RealMatchTeam


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
        Joins with RealMatchTeams to reconstruct first/second team fields.
        """
        where_clauses = ["1=1"]
        params: dict = {}

        if real_competition_id is not None:
            where_clauses.append("realCompetitionID = :realCompetitionID")
            params["realCompetitionID"] = real_competition_id

        if real_competition_match_day is not None:
            where_clauses.append("realCompetitionMatchDay = :realCompetitionMatchDay")
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
            WHERE {' AND '.join(where_clauses)}
            ORDER BY realMatchDate ASC
        """)

        matches = [dict(r) for r in db.execute(sql, params).mappings()]

        def to_iso(val):
            if val is None:
                return None
            if isinstance(val, str):
                return val
            return val.isoformat()

        items = []
        for match in matches:
            # Query RealMatchTeams for this match to get team data
            team_records = db.query(RealMatchTeam).filter(
                RealMatchTeam.realMatchID == match["realMatchID"]
            ).all()

            # Create a dict keyed by realTeamNumber
            teams_by_num = {rmt.realTeamNumber: rmt for rmt in team_records}

            values = {
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
            }

            # Add first team data (realTeamNumber = 1)
            if 1 in teams_by_num:
                rmt1 = teams_by_num[1]
                values.update({
                    "firstRealTeamMemberID": rmt1.realTeamMemberID,
                    "firstRealTeamMemberKey": rmt1.realTeamMemberKey,
                    "firstRealTeamID": rmt1.realTeamID,
                    "firstRealTeamUID": rmt1.realTeamUID,
                    "firstRealTeamName": rmt1.realTeamName,
                    "firstRealTeamShortName": rmt1.realTeamShortName,
                    "firstRealTeamScore": rmt1.realTeamScore,
                    "firstRealTeamRealScore": rmt1.realTeamRealScore,
                    "firstRealTeamSide": rmt1.realTeamSide,
                    "firstRealTeamCleanSheet": rmt1.realTeamCleanSheet,
                    "firstRealTeamResult": rmt1.realTeamResult,
                    "firstRealTeamPoints": rmt1.realTeamPoints,
                    "firstRealTeamNumber": rmt1.realTeamNumber,
                })
            else:
                values.update({
                    "firstRealTeamMemberID": None,
                    "firstRealTeamMemberKey": None,
                    "firstRealTeamID": None,
                    "firstRealTeamUID": None,
                    "firstRealTeamName": None,
                    "firstRealTeamShortName": None,
                    "firstRealTeamScore": None,
                    "firstRealTeamRealScore": None,
                    "firstRealTeamSide": None,
                    "firstRealTeamCleanSheet": None,
                    "firstRealTeamResult": None,
                    "firstRealTeamPoints": None,
                    "firstRealTeamNumber": None,
                })

            # Add second team data (realTeamNumber = 2)
            if 2 in teams_by_num:
                rmt2 = teams_by_num[2]
                values.update({
                    "secondRealTeamMemberID": rmt2.realTeamMemberID,
                    "secondRealTeamMemberKey": rmt2.realTeamMemberKey,
                    "secondRealTeamID": rmt2.realTeamID,
                    "secondRealTeamUID": rmt2.realTeamUID,
                    "secondRealTeamName": rmt2.realTeamName,
                    "secondRealTeamShortName": rmt2.realTeamShortName,
                    "secondRealTeamScore": rmt2.realTeamScore,
                    "secondRealTeamRealScore": rmt2.realTeamRealScore,
                    "secondRealTeamSide": rmt2.realTeamSide,
                    "secondRealTeamCleanSheet": rmt2.realTeamCleanSheet,
                    "secondRealTeamResult": rmt2.realTeamResult,
                    "secondRealTeamPoints": rmt2.realTeamPoints,
                    "secondRealTeamNumber": rmt2.realTeamNumber,
                })
            else:
                values.update({
                    "secondRealTeamMemberID": None,
                    "secondRealTeamMemberKey": None,
                    "secondRealTeamID": None,
                    "secondRealTeamUID": None,
                    "secondRealTeamName": None,
                    "secondRealTeamShortName": None,
                    "secondRealTeamScore": None,
                    "secondRealTeamRealScore": None,
                    "secondRealTeamSide": None,
                    "secondRealTeamCleanSheet": None,
                    "secondRealTeamResult": None,
                    "secondRealTeamPoints": None,
                    "secondRealTeamNumber": None,
                })

            # Add metadata
            values.update({
                "enabled": match["enabled"],
                "lastF7Date": to_iso(match["lastF7Date"]),
                "lastF42Date": to_iso(match["lastF42Date"]),
                "lastFDate": to_iso(match["lastFDate"]),
                "createdIn": to_iso(match["createdIn"]),
                "updatedIn": to_iso(match["updatedIn"]),
            })

            items.append(values)

        return items
