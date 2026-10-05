import functools
from collections.abc import Iterator
from datetime import datetime

from sqlalchemy import Row, select
from sqlalchemy.orm import Session

from app.constants import CompetitionTypeConstants, MatchStatusConstants
from app.models import Match, MatchDaysStatus, MatchTeam, Team
from app.services import QueryService
from app.utils.dt import utc_now
from app.utils.lineup import Lineup
from app.utils.readers import RSReader


class SettleMatches:
    def __init__(self, db: Session, reader: RSReader):
        self._db = db
        self._reader = reader
        self._base_rc_id: int | None = None
        self._extra_rc_id: int | None = None
        self._rc_id: int | None = None
        self._rc_md: int | None = None
        self._rc_md_sort: int | None = None
        self._sides = ["Home", "Away"]
        self._standings: dict[int, dict] = {}
        self._standings_fields = [
            "won",
            "draw",
            "lost",
            "scoreFor",
            "scoreAgainst",
            "points",
        ]
        self._next_group_fields = ["teamID", "teamName", "teamSeeding", "mapDayMapKey"]

    def execute(self, rc_id: int | None = None, now: datetime | None = None) -> None:
        self._base_rc_id = QueryService.get_base_competition_id(self._db, rc_id)
        self._extra_rc_id = QueryService.get_extra_competition_id(self._db, rc_id)
        now = utc_now() if now is None else now
        if self._get_match_day(now):
            self._process_rr()
            self._process_ko()

    def _get_match_day(self, now: datetime) -> bool:
        row = self._db.execute(
            select(
                MatchDaysStatus.realCompetitionID,
                MatchDaysStatus.realCompetitionMatchDay,
                MatchDaysStatus.realCompetitionMatchDaySort,
            )
            .where(
                MatchDaysStatus.baseRealCompetitionID == self._base_rc_id,
                MatchDaysStatus.active == 1,
                MatchDaysStatus.startPostMatch <= now,
                MatchDaysStatus.finishPostMatch > now,
            )
            .distinct()
        ).first()
        if row:
            self._rc_id = row.realCompetitionID
            self._rc_md = row.realCompetitionMatchDay
            self._rc_md_sort = row.realCompetitionMatchDaySort
            return True
        else:
            self._rc_id = None
            self._rc_md = None
            self._rc_md_sort = None
            return False

    def _process_rr(self) -> None:
        for matches in self._read_matches_for_rr():
            self._settle_matches_rr(matches)
            self._save_matches_rr(matches)

    def _process_ko(self) -> None:
        for groups in self._read_groups_for_ko():
            self._settle_matches_ko(groups)
            self._save_matches_ko(groups)

    def _settle_matches_rr(self, matches: dict[int, dict]) -> None:
        invalid = [k for k, m in matches.items() if "Home" not in m or "Away" not in m]
        for k in invalid:
            del matches[k]
        is_curr = False
        for match in matches.values():
            if match["is_curr"]:
                is_curr = True
                self._settle_match(match)
                self._calc_standings_rr(match)
        if is_curr:
            self._calc_places_rr(matches)

    def _save_matches_rr(self, matches: dict[int, dict]) -> None:
        now = utc_now()
        for match_id, match in matches.items():
            if any(side not in match for side in self._sides):
                continue
            is_curr = match.get("is_curr", False)
            if is_curr:
                m = self._db.get(Match, match_id)
                if m:
                    m.matchStatus = MatchStatusConstants.FINISHED
                    m.updatedIn = now
            cnt_teams = len(self._standings)
            for side in self._sides:
                side_data = match.get(side)
                if not side_data:
                    continue
                s = self._standings.get(side_data["teamID"])
                if not s:
                    continue
                mt = self._db.get(MatchTeam, side_data["matchTeamID"])
                if mt:
                    if is_curr:
                        mt.lineup = side_data["lineup"]
                        mt.teamScore = side_data["teamScore"]
                        mt.teamPoints = side_data["teamPoints"]
                        t = self._db.get(Team, side_data["teamID"])
                        if t:
                            t.waiversOrder = 1 + cnt_teams - s["place"]
                            t.updatedIn = now
                    else:
                        mt.teamScore = None
                        mt.teamPoints = None
                    for key, val in s.items():
                        if key != "teamID":
                            setattr(mt, key, val)
                    mt.updatedIn = now
        self._db.commit()

    def _settle_matches_ko(self, groups: dict) -> None:
        for group in groups["curr"]:
            self._settle_match(group["match"])
            if group["is_last_round"]:
                self._settle_group_ko(group)
                self._append_to_next_group_ko(groups["next"], group)
        for group in groups["next"].values():
            self._complete_next_group_ko(group)

    def _save_matches_ko(self, groups: dict) -> None:
        now = utc_now()
        for group in groups["curr"]:
            match = group["match"]
            m = self._db.get(Match, match["matchID"])
            if m:
                m.matchStatus = MatchStatusConstants.FINISHED
                m.updatedIn = now
            for side in self._sides:
                side_data = match.get(side)
                if not side_data:
                    continue
                mt = self._db.get(MatchTeam, side_data["matchTeamID"])
                if mt:
                    mt.lineup = side_data["lineup"]
                    mt.teamScore = side_data["teamScore"]
                    mt.teamPoints = side_data["teamPoints"]
                    if group["is_last_round"]:
                        mt.matchGroupWinnerTeamID = side_data["matchGroupWinnerTeamID"]
                    mt.updatedIn = now
            if group["is_last_round"]:
                for prior in group["group"]:
                    for side in self._sides:
                        side_data = prior.get(side)
                        if not side_data:
                            continue
                        mt = self._db.get(MatchTeam, side_data["matchTeamID"])
                        if mt:
                            mt.matchGroupWinnerTeamID = side_data[
                                "matchGroupWinnerTeamID"
                            ]
                            mt.updatedIn = now
        for matches in groups["next"].values():
            for match in matches:
                for side in self._sides:
                    side_data = match.get(side)
                    if not side_data:
                        continue
                    mt = self._db.get(MatchTeam, side_data["matchTeamID"])
                    if mt:
                        for f in self._next_group_fields:
                            setattr(mt, f, side_data[f])
                        mt.updatedIn = now
        self._db.commit()

    def _settle_match(self, match: dict) -> None:
        lineup_h = Lineup(self._reader, True)
        lineup_h.unpack(match["Home"]["lineup"], match["Home"]["teamMembers"])
        lineup_a = Lineup(self._reader, True)
        lineup_a.unpack(match["Away"]["lineup"], match["Away"]["teamMembers"])
        score_h = lineup_h.score()
        score_a = lineup_a.score()
        if score_h > score_a:
            match["Home"]["teamPoints"] = 3
            match["Away"]["teamPoints"] = 0
        elif score_a > score_h:
            match["Away"]["teamPoints"] = 3
            match["Home"]["teamPoints"] = 0
        else:
            match["Home"]["teamPoints"] = 1
            match["Away"]["teamPoints"] = 1
        match["Home"]["teamScore"] = score_h
        match["Away"]["teamScore"] = score_a
        match["Home"]["lineup"] = lineup_h.pack()
        match["Away"]["lineup"] = lineup_a.pack()

    def _calc_standings_rr(self, match: dict) -> None:
        for i, side in enumerate(self._sides):
            op_side = self._sides[1 - i]
            t_id = match[side]["teamID"]
            if t_id not in self._standings:
                self._standings[t_id] = {}
                for s in [""] + self._sides:
                    for f in self._standings_fields:
                        self._standings[t_id][f + s] = 0
            results = {
                "won": 1 if match[side]["teamPoints"] == 3 else 0,
                "draw": 1 if match[side]["teamPoints"] == 1 else 0,
                "lost": 1 if match[side]["teamPoints"] == 0 else 0,
                "scoreFor": match[side]["teamScore"],
                "scoreAgainst": match[op_side]["teamScore"],
                "points": match[side]["teamPoints"],
            }
            for s in ["", side]:
                for f in self._standings_fields:
                    self._standings[t_id][f + s] += results.get(f, 0)

    def _calc_places_rr(self, matches: dict[int, dict]) -> None:
        mt = []
        for match in matches.values():
            for i, side in enumerate(self._sides):
                op_side = self._sides[1 - i]
                scoreFor = match[side]["teamScore"]
                scoreAgainst = match[op_side]["teamScore"]
                mt.append(
                    {
                        "matchID": match["matchID"],
                        "side": side,
                        "teamID": match[side]["teamID"],
                        "name": match[side]["teamName"],
                        "seeding": match[side]["teamSeeding"],
                        "order": [
                            match[side]["teamPoints"],
                            scoreFor - scoreAgainst,
                            scoreFor,
                        ],
                    }
                )
        mt.sort(key=functools.cmp_to_key(self._compare_rr))
        for i, x in enumerate(mt):
            self._standings[x["teamID"]]["place"] = i + 1

    def _compare_rr(self, a: dict, b: dict) -> int:
        for i, (x, y) in enumerate(zip(a["order"], b["order"])):
            if x > y:
                return -1
            elif x < y:
                return 1
        if a["name"] < b["name"]:
            return -1
        elif a["name"] > b["name"]:
            return 1
        if a["seeding"] < b["seeding"]:
            return -1
        return 1

    def _settle_group_ko(self, group: dict) -> None:
        points_h = group["match"]["Home"]["teamPoints"]
        points_a = group["match"]["Away"]["teamPoints"]
        score_h = group["match"]["Home"]["teamScore"]
        score_a = group["match"]["Away"]["teamScore"]
        for match in group["group"]:
            for side in self._sides:
                if group["match"]["Home"]["teamID"] == match[side]["teamID"]:
                    points_h += match[side]["teamPoints"]
                    score_h += match[side]["teamScore"]
                else:
                    points_a += match[side]["teamPoints"]
                    score_a += match[side]["teamScore"]
        team_id_home = group["match"]["Home"]["teamID"]
        team_id_away = group["match"]["Away"]["teamID"]
        if points_h > points_a:
            # matchGroupWinnerTeamID
            winner = team_id_home
        elif points_a > points_h:
            winner = team_id_away
        elif score_h > score_a:
            winner = team_id_home
        elif score_a > score_h:
            winner = team_id_away
        elif (
            group["match"]["Home"]["teamPoints"] > group["match"]["Away"]["teamPoints"]
        ):
            winner = team_id_home
        elif (
            group["match"]["Away"]["teamPoints"] > group["match"]["Home"]["teamPoints"]
        ):
            winner = team_id_away
        elif group["match"]["Home"]["teamScore"] > group["match"]["Away"]["teamScore"]:
            winner = team_id_home
        elif group["match"]["Away"]["teamScore"] > group["match"]["Home"]["teamScore"]:
            winner = team_id_away
        elif (
            group["match"]["Home"]["teamSeeding"]
            < group["match"]["Away"]["teamSeeding"]
        ):
            winner = team_id_home
        else:
            winner = team_id_away
        group["match"]["Home"]["matchGroupWinnerTeamID"] = winner
        group["match"]["Away"]["matchGroupWinnerTeamID"] = winner
        for i, match in enumerate(group["group"]):
            group["group"][i]["Home"]["matchGroupWinnerTeamID"] = winner
            group["group"][i]["Away"]["matchGroupWinnerTeamID"] = winner

    def _append_to_next_group_ko(
        self, next_group: dict[int, list[dict]], group: dict
    ) -> None:
        if len(next_group) > 0:
            match = group["match"]
            gr = match["competitionMatchNextGroup"]
            if gr in next_group:
                src = (
                    "Home"
                    if match["Home"]["teamID"]
                    == match["Home"]["matchGroupWinnerTeamID"]
                    else "Away"
                )
                tgt = "Home" if next_group[gr][0]["Home"]["teamID"] is None else "Away"
                for f in self._next_group_fields:
                    next_group[gr][0][tgt][f] = match[src][f]

    def _complete_next_group_ko(self, group: list[dict]) -> None:
        fields = self._next_group_fields
        if group[0]["Home"]["teamSeeding"] > group[0]["Away"]["teamSeeding"]:
            for f in fields:
                group[0]["Home"][f], group[0]["Away"][f] = (
                    group[0]["Away"][f],
                    group[0]["Home"][f],
                )
        s = 1
        for i in range(1, len(group)):
            for f in fields:
                group[i]["Home"][f] = group[0][self._sides[s]][f]
                group[i]["Away"][f] = group[0][self._sides[1 - s]][f]
            s = 1 - s

    def _read_matches_for_rr(self) -> Iterator[dict[int, dict]]:
        matches: dict[int, dict] = {}
        div_id = None
        rc_id = None
        rc_md = None
        after_md = False
        for row in self._read_row_for_rr():
            if div_id != row.divisionID:
                if matches and after_md:
                    yield matches
                matches = {}
                self._standings = {}
                div_id = row.divisionID
                rc_id = row.realCompetitionID
                rc_md = row.realCompetitionMatchDay
                after_md = False
            if rc_id != row.realCompetitionID or rc_md != row.realCompetitionMatchDay:
                if after_md:
                    yield matches
                matches = {}
                rc_id = row.realCompetitionID
                rc_md = row.realCompetitionMatchDay
            try:
                side = self._sides[row.matchTeamNum - 1]
            except IndexError:
                continue
            is_curr = rc_id == self._rc_id and rc_md == self._rc_md
            if is_curr:
                after_md = True
            elif not after_md:
                self._copy_standings_rr(row)
                continue
            m_id = row.matchID
            if m_id not in matches:
                matches[m_id] = {
                    "matchID": m_id,
                    "divisionID": row.divisionID,
                    "is_curr": is_curr,
                }
            elif side in matches[row.matchID]:
                continue
            matches[m_id][side] = {
                "teamID": row.teamID,
                "teamName": row.teamName,
                "teamSeeding": row.teamSeeding,
                "matchTeamID": row.matchTeamID,
                "lineup": row.lineup,
                "teamMembers": row.teamMembers,
            }
        if matches and after_md:
            yield matches

    def _read_row_for_rr(self) -> Iterator[Row]:
        yield from self._db.execute(
            select(
                Match.matchID,
                Match.divisionID,
                Match.realCompetitionID,
                Match.realCompetitionMatchDay,
                Match.competitionMatchDay,
                MatchTeam.matchTeamID,
                MatchTeam.teamID,
                MatchTeam.teamName,
                MatchTeam.lineup,
                MatchTeam.matchTeamNum,
                MatchTeam.teamSeeding,
                MatchTeam.won,
                MatchTeam.draw,
                MatchTeam.lost,
                MatchTeam.scoreFor,
                MatchTeam.scoreAgainst,
                MatchTeam.points,
                MatchTeam.wonHome,
                MatchTeam.drawHome,
                MatchTeam.lostHome,
                MatchTeam.scoreForHome,
                MatchTeam.scoreAgainstHome,
                MatchTeam.pointsHome,
                MatchTeam.wonAway,
                MatchTeam.drawAway,
                MatchTeam.lostAway,
                MatchTeam.scoreForAway,
                MatchTeam.scoreAgainstAway,
                MatchTeam.pointsAway,
                Team.teamMembers,
            )
            .join(MatchTeam, MatchTeam.matchID == Match.matchID)
            .join(Team, Team.teamID == MatchTeam.teamID)
            .where(
                Match.competitionType == CompetitionTypeConstants.DIVISION_ROUND_ROBIN,
                Match.realCompetitionID.in_([self._base_rc_id, self._extra_rc_id]),
            )
            .order_by(
                Match.divisionID,
                Match.realCompetitionMatchDay,
                Match.competitionMatchDay,
            )
        )

    def _copy_standings_rr(self, row: Row) -> None:
        if row.teamID not in self._standings:
            self._standings[row.teamID] = {}
        for s in [""] + self._sides:
            for f in self._standings_fields:
                self._standings[row.teamID][f + s] = getattr(row, f + s)

    def _read_groups_for_ko(self) -> Iterator[dict]:
        for matches in self._read_all_matches_for_ko():
            groups = {}
            curr_idx = []
            next_idx = set()
            for i, match in enumerate(matches):
                gr = match["competitionMatchGroup"]
                if gr not in groups:
                    groups[gr] = []
                if (
                    match["realCompetitionID"] == self._rc_id
                    and match["realCompetitionMatchDay"] == self._rc_md
                ):
                    curr_idx.append(i)
                    if match["competitionMatchNextGroup"] is not None:
                        next_idx.add(match["competitionMatchNextGroup"])
                else:
                    groups[gr].append(i)
            if curr_idx:
                curr_groups = []
                next_groups = {}
                for i in curr_idx:
                    match = matches[i]
                    is_last = False
                    group = []
                    if (
                        match["competitionMatchRound"]
                        == match["competitionMatchLastRound"]
                    ):
                        is_last = True
                        for j in groups[match["competitionMatchGroup"]]:
                            self._add_to_group_ko(group, matches[j])
                    curr_groups.append(
                        {"match": match, "is_last_round": is_last, "group": group}
                    )
                for gr in next_idx:
                    next_groups[gr] = []
                    for j in groups[gr]:
                        self._add_to_group_ko(next_groups[gr], matches[j])
                yield {"curr": curr_groups, "next": next_groups}

    def _add_to_group_ko(self, group: list, match: dict) -> None:
        if len(group) == 0 or match["matchID"] > group[-1]["matchID"]:
            group.append(match)
        else:
            for i in range(len(group)):
                if match["matchID"] < group[i]["matchID"]:
                    group.insert(i, match)
                    return

    def _read_all_matches_for_ko(self) -> Iterator[list[dict]]:
        matches: dict[int, dict] = {}
        lea_id = None
        div_id = None
        for row in self._read_row_for_ko():
            if lea_id != row.leagueID or div_id != row.divisionID:
                if matches:
                    yield list(matches.values())
                matches = {}
                lea_id = row.leagueID
                div_id = row.divisionID
            try:
                side = self._sides[row.matchTeamNum - 1]
            except IndexError:
                continue
            m_id = row.matchID
            if m_id not in matches:
                matches[m_id] = {
                    "matchID": m_id,
                    "leagueID": row.leagueID,
                    "divisionID": row.divisionID,
                    "realCompetitionID": row.realCompetitionID,
                    "realCompetitionMatchDay": row.realCompetitionMatchDay,
                    "competitionMatchDay": row.competitionMatchDay,
                    "competitionMatchNumber": row.competitionMatchNumber,
                    "competitionMatchGroup": row.competitionMatchGroup,
                    "competitionMatchNextGroup": row.competitionMatchNextGroup,
                    "competitionMatchRound": row.competitionMatchRound,
                    "competitionMatchLastRound": row.competitionMatchLastRound,
                }
            elif side in matches[row.matchID]:
                continue
            matches[m_id][side] = {
                "teamID": row.teamID,
                "teamName": row.teamName,
                "matchTeamID": row.matchTeamID,
                "lineup": row.lineup,
                "teamMembers": row.teamMembers,
                "mapDayMapKey": row.mapDayMapKey,
                "teamSeeding": row.teamSeeding,
                "teamScore": row.teamScore,
                "teamPoints": row.teamPoints,
            }
        if matches:
            yield list(matches.values())

    def _read_row_for_ko(self) -> Iterator[Row]:
        yield from self._db.execute(
            select(
                Match.matchID,
                Match.leagueID,
                Match.divisionID,
                Match.realCompetitionID,
                Match.realCompetitionMatchDay,
                Match.competitionMatchDay,
                Match.competitionMatchNumber,
                Match.competitionMatchGroup,
                Match.competitionMatchNextGroup,
                Match.competitionMatchRound,
                Match.competitionMatchLastRound,
                MatchTeam.matchTeamID,
                MatchTeam.teamID,
                MatchTeam.teamName,
                MatchTeam.lineup,
                MatchTeam.matchTeamNum,
                Team.teamMembers,
                MatchTeam.mapDayMapKey,
                MatchTeam.teamSeeding,
                MatchTeam.teamScore,
                MatchTeam.teamPoints,
            )
            .join(MatchTeam, MatchTeam.matchID == Match.matchID)
            .join(Team, Team.teamID == MatchTeam.teamID)
            .where(
                Match.competitionType.in_(
                    [
                        CompetitionTypeConstants.DIVISION_KNOCK_OUT,
                        CompetitionTypeConstants.LEAGUE_KNOCK_OUT,
                    ]
                ),
                Match.realCompetitionID.in_([self._base_rc_id, self._extra_rc_id]),
            )
            .order_by(
                Match.leagueID,
                Match.divisionID,
                Match.competitionMatchDay,
                Match.matchID,
            )
        )
