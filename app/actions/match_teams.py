from datetime import datetime

from sqlalchemy import text
from sqlalchemy.engine import RowMapping
from sqlalchemy.orm import Session

from app.constants import MatchStatusConstants
from app.context import RequestContext
from app.guards import require_league_member, require_team_owner
from app.models import Match, MatchTeam
from app.services.query import QueryService
from app.utils.dt import to_iso
from app.utils.lineup import Lineup
from app.utils.readers import RSReader

_LINEUP_SQL = """
    SELECT `mt`.`matchTeamID`,
           `mt`.`matchID`,
           `mt`.`userID`,
           `mt`.`teamID`,
           `mt`.`matchTeamNum`,
           `m`.`realCompetitionID`,
           `m`.`realCompetitionMatchDay`,
           `m`.`realCompetitionMatchDaySort`,
           `m`.`matchStatus`,
           `m`.`competitionType`,
           `m`.`competitionMatchDay`,
           `mt`.`matchDayMapKey`,
           `mt`.`lineup`,
           `t`.`teamMembers`
       FROM `MatchTeams` `mt`
       INNER JOIN `Matches` `m` ON `m`.`matchID` = `mt`.`matchID`
       LEFT OUTER JOIN `Teams` `t` ON `t`.`teamID` = `mt`.`teamID`
"""


def read_lineup_by_match_team(db: Session, match_team_id: int) -> RowMapping | None:
    sql = _LINEUP_SQL + "WHERE `mt`.`matchTeamID` = :matchTeamID"
    return db.execute(text(sql), {"matchTeamID": match_team_id}).mappings().first()


def read_lineup_by_team_id(
    db: Session,
    team_id: int,
    competition_type: int,
    competition_match_day: int,
) -> RowMapping | None:
    sql = (
        _LINEUP_SQL
        + "WHERE `mt`.`teamID` = :teamID"
        + "  AND `m`.`competitionType` = :competitionType"
        + "  AND `m`.`competitionMatchDay` = :competitionMatchDay"
    )
    return (
        db.execute(
            text(sql),
            {
                "teamID": team_id,
                "competitionType": competition_type,
                "competitionMatchDay": competition_match_day,
            },
        )
        .mappings()
        .first()
    )


def read_prev_lineup(
    db: Session,
    team_id: int,
    competition_type: int,
    competition_match_day: int,
) -> str | None:
    sql = """
        SELECT `lineup`
           FROM `MatchTeams` `mt`
           INNER JOIN `Matches` `m` ON `m`.`matchID` = `mt`.`matchID`
           WHERE `mt`.`teamID` = :teamID
             AND `m`.`competitionType` = :competitionType
             AND `m`.`competitionMatchDay` < :competitionMatchDay
           ORDER BY `m`.`competitionMatchDay` DESC
    """
    rows = db.execute(
        text(sql),
        {
            "teamID": team_id,
            "competitionType": competition_type,
            "competitionMatchDay": competition_match_day,
        },
    ).mappings().all()
    for row in rows:
        if not Lineup.is_empty(row["lineup"]):
            lineup_txt = Lineup.clean_up(row["lineup"])
            if lineup_txt is not None:
                return lineup_txt
    return None


def read_lineups_by_match_ids(db: Session, match_ids: list[int]) -> list[RowMapping]:
    params = {f"id{i}": v for i, v in enumerate(match_ids)}
    placeholders = ",".join(f":id{i}" for i in range(len(match_ids)))
    sql = _LINEUP_SQL + f"WHERE `mt`.`matchID` IN ({placeholders}) ORDER BY `mt`.`matchID`, `mt`.`matchTeamID`"
    return list(db.execute(text(sql), params).mappings().all())


def read_lineups_by_match_day(
    db: Session,
    competition_type: int,
    competition_match_day: int,
    league_id: int,
    division_id: int | None = None,
) -> list[RowMapping]:
    from app.constants import CompetitionTypeConstants
    sql = (
        _LINEUP_SQL
        + "WHERE `m`.`competitionType` = :competitionType"
        + "  AND `m`.`competitionMatchDay` = :competitionMatchDay"
        + "  AND `m`.`leagueID` = :leagueID"
    )
    params: dict = {
        "competitionType": competition_type,
        "competitionMatchDay": competition_match_day,
        "leagueID": league_id,
    }
    if competition_type != CompetitionTypeConstants.LEAGUE_KNOCK_OUT:
        sql += "  AND `m`.`divisionID` = :divisionID"
        params["divisionID"] = division_id
    sql += " ORDER BY `mt`.`matchID`, `mt`.`matchTeamID`"
    return list(db.execute(text(sql), params).mappings().all())


def save_lineup(db: Session, match_team_id: int, lineup_txt: str) -> None:
    db.execute(
        text("UPDATE `MatchTeams` SET `lineup` = :lineup WHERE `matchTeamID` = :matchTeamID"),
        {"lineup": lineup_txt, "matchTeamID": match_team_id},
    )


def save_match_status(db: Session, match_id: int, match_status: int) -> None:
    db.execute(
        text("UPDATE `Matches` SET `matchStatus` = :matchStatus WHERE `matchID` = :matchID"),
        {"matchStatus": match_status, "matchID": match_id},
    )


class MatchTeamsReadListAction:
    """Handle MatchTeams ReadList requests."""

    @staticmethod
    def execute(db: Session, team_id: int, user_id: int | None = None) -> dict:
        """Get match teams for a team (matches where the team participated)."""
        require_league_member(db, user_id, team_id=team_id)
        match_teams = (
            db.query(MatchTeam)
            .filter(MatchTeam.teamID == team_id)
            .order_by(MatchTeam.matchID, MatchTeam.matchTeamNum)
            .all()
        )

        items: list[dict] = []
        match: Match | None = None
        pair: list[dict] = []
        for mt in match_teams:
            if match is None or match.matchID != mt.matchID:
                MatchTeamsReadListAction._add_match(items, match, pair)
                match = db.query(Match).filter(Match.matchID == mt.matchID).first()
                pair = []
            pair.append(mt.model_dump())
        MatchTeamsReadListAction._add_match(items, match, pair)

        return items

    @staticmethod
    def _add_match(items: list[dict], match: Match | None, pair: list[dict]) -> None:
        if match is not None:
            op = pair[1] if len(pair) > 1 else None
            MatchTeamsReadListAction._add_mt(items, match, pair[0], op)
            if op is not None:
                MatchTeamsReadListAction._add_mt(items, match, op, pair[0])

    @staticmethod
    def _add_mt(items: list[dict], match: Match, mt: dict, mt_op: dict | None) -> None:
        mt_op = mt_op or {}
        items.append({
            "matchTeamID": mt["matchTeamID"],
            "matchID": mt["matchID"],
            "matchTeamNum": mt["matchTeamNum"],
            "matchStatus": match.matchStatus,
            "leagueID": match.leagueID,
            "divisionID": match.divisionID,
            "season": match.season,
            "seasonNum": match.seasonNum,
            "realCompetitionID": match.realCompetitionID,
            "realCompetitionMatchDay": match.realCompetitionMatchDay,
            "realCompetitionMatchDaySort": match.realCompetitionMatchDaySort,
            "competitionType": match.competitionType,
            "competitionMatchDay": match.competitionMatchDay,
            "competitionLastMatchDay": match.competitionLastMatchDay,
            "competitionMatchNumber": match.competitionMatchNumber,
            "competitionMatchGroup": match.competitionMatchGroup,
            "competitionMatchNextGroup": match.competitionMatchNextGroup,
            "competitionMatchRound": match.competitionMatchRound,
            "competitionMatchLastRound": match.competitionMatchLastRound,
            "matchGroupWinnerTeamID": match.matchGroupWinnerTeamID,
            "userID": mt["userID"],
            "teamID": mt["teamID"],
            "teamName": mt["teamName"],
            "teamScore": mt["teamScore"],
            "teamPoints": mt["teamPoints"],
            "teamSeeding": mt["teamSeeding"],
            "matchDayMapKey": mt["matchDayMapKey"],
            "oppositeUserID": mt_op["userID"] if mt_op else None,
            "oppositeTeamID": mt_op["teamID"] if mt_op else None,
            "oppositeTeamName": mt_op["teamName"] if mt_op else None,
            "oppositeTeamScore": mt_op["teamScore"] if mt_op else None,
            "oppositeTeamPoints": mt_op["teamPoints"] if mt_op else None,
            "oppositeTeamSeeding": mt_op["teamSeeding"] if mt_op else None,
            "oppositeMatchDayMapKey": mt_op["matchDayMapKey"] if mt_op else None,
            "lineup": mt["lineup"],
            "cntEPLTeam": mt["cntEPLTeam"],
            "cntGoalkeeper": mt["cntGoalkeeper"],
            "cntDefender": mt["cntDefender"],
            "cntMidfielder": mt["cntMidfielder"],
            "cntStriker": mt["cntStriker"],
            "cntSubstitute": mt["cntSubstitute"],
            "cntInactive": mt["cntInactive"],
            "createdBy": mt["createdBy"],
            "createdIn": to_iso(mt["createdIn"]),
            "updatedBy": mt["updatedBy"],
            "updatedIn": to_iso(mt["updatedIn"]),
        })


class GetLineupAction:
    """Handle MatchTeams GetLineup requests."""

    @staticmethod
    def _execute(
        db: Session,
        match_team_id: int | None = None,
        team_id: int | None = None,
        competition_type: int | None = None,
        competition_match_day: int | None = None,
        new_lineup: str | None = None,
        save: bool = False,
    ) -> dict | None:
        if match_team_id is not None:
            match_team = read_lineup_by_match_team(db, match_team_id)
        elif (
            team_id is not None
            and competition_type is not None
            and competition_match_day is not None
        ):
            match_team = read_lineup_by_team_id(
                db, team_id, competition_type, competition_match_day
            )
        else:
            raise ValueError(
                "Either match_team_id or (team_id, competition_type, competition_match_day) must be provided"
            )
        if match_team is None:
            return None

        reader = RSReader(
            db,
            match_team["realCompetitionID"],
            match_team["realCompetitionMatchDay"],
        )

        now = RequestContext.get_datetime()
        match_status = _get_match_status(db, match_team, now)

        if new_lineup is not None and match_status != MatchStatusConstants.NOT_STARTED:
            return None

        prev_lineup = None
        if (
            new_lineup is None
            and Lineup.is_empty(match_team.get("lineup"))
            and match_status != MatchStatusConstants.FINISHED
        ):
            prev_lineup = read_prev_lineup(
                db,
                match_team["teamID"],
                match_team["competitionType"],
                match_team["competitionMatchDay"],
            )

        lineup_txt = Lineup.clean_up(
            new_lineup or match_team["lineup"] or prev_lineup or ""
        )
        if lineup_txt is None:
            return None

        team_members = (
            match_team["teamMembers"]
            if match_status != MatchStatusConstants.FINISHED
            else None
        )
        lineup = Lineup(reader, match_started=(match_status == MatchStatusConstants.PLAYING))
        if not lineup.unpack(lineup_txt, team_members):
            return None

        if save:
            if not lineup.is_equal(lineup_txt):
                save_lineup(db, match_team["matchTeamID"], lineup.pack())
            db.commit()

        return list(lineup.get_members(
            matchTeamID=match_team["matchTeamID"],
            teamID=match_team["teamID"],
            matchStatus=match_status,
        ))


class GetLineupByMatchTeamIDAction(GetLineupAction):
    """Handle MatchTeams GetLineupByMatchTeamID requests."""

    @staticmethod
    def execute(db: Session, match_team_id: int) -> dict | None:
        return GetLineupAction._execute(db, match_team_id=match_team_id)


class GetLineupByCompetitionTypeAction:
    """Handle MatchTeams GetLineupByCompetitionType requests."""

    @staticmethod
    def execute(
        db: Session,
        team_id: int,
        competition_type: int,
        competition_match_day: int,
        user_id: int | None = None,
    ) -> dict | None:
        require_league_member(db, user_id, team_id=team_id)
        return GetLineupAction._execute(
            db,
            team_id=team_id,
            competition_type=competition_type,
            competition_match_day=competition_match_day,
        )


class SetLineupByCompetitionTypeAction(GetLineupAction):
    """Handle MatchTeams SetLineupByCompetitionType requests."""

    @staticmethod
    def execute(
        db: Session,
        team_id: int,
        competition_type: int,
        competition_match_day: int,
        real_team_id: int,
        real_player_ids: list[int],
        substitute_real_player_ids: list[int],
        user_id: int | None = None,
    ) -> dict | None:
        require_team_owner(db, user_id, team_id)
        new_lineup = Lineup.from_ids(
            real_team_id, real_player_ids, substitute_real_player_ids
        )
        return GetLineupAction._execute(
            db,
            team_id=team_id,
            competition_type=competition_type,
            competition_match_day=competition_match_day,
            new_lineup=new_lineup,
            save=True,
        )


class ClearLineupByMatchTeamIDAction:
    """Handle MatchTeams ClearLineupByMatchTeamID requests."""

    @staticmethod
    def execute(db: Session, match_team_id: int, user_id: int) -> dict | None:
        match_team = (
            db.query(MatchTeam).filter(MatchTeam.matchTeamID == match_team_id).first()
        )
        if match_team is None:
            return None
        if match_team.userID != user_id:
            raise PermissionError
        db.execute(
            text(
                "UPDATE `MatchTeams` SET `lineup` = '' WHERE `matchTeamID` = :matchTeamID"
            ),
            {"matchTeamID": match_team_id},
        )
        db.commit()
        return {"matchTeamID": match_team_id}


class GetScores:
    @staticmethod
    def _execute(
        db: Session,
        match_ids: list[int] | None = None,
        competition_type: int | None = None,
        competition_match_day: int | None = None,
        league_id: int | None = None,
        division_id: int | None = None,
    ) -> list | None:
        if match_ids is not None:
            match_teams = read_lineups_by_match_ids(db, match_ids)
        elif (
            competition_type is not None
            and competition_match_day is not None
            and league_id is not None
        ):
            match_teams = read_lineups_by_match_day(
                db, competition_type, competition_match_day, league_id, division_id
            )
        else:
            raise ValueError(
                "Either match_ids or (competition_type, competition_match_day, league_id) must be provided"
            )
        if not match_teams:
            return None

        reader = RSReader(
            db,
            match_teams[0]["realCompetitionID"],
            match_teams[0]["realCompetitionMatchDay"],
        )

        now = RequestContext.get_datetime()
        match_status = _get_match_status(db, match_teams[0], now)

        results = []
        for match_team in match_teams:
            lineup = Lineup(reader, match_started=(match_status == MatchStatusConstants.PLAYING))
            lineup_txt = Lineup.clean_up(match_team["lineup"] or "")
            if lineup_txt is not None:
                team_members = (
                    match_team["teamMembers"]
                    if match_status != MatchStatusConstants.FINISHED
                    else None
                )
                lineup.unpack(lineup_txt, team_members)
            results.append({
                "matchTeamID": match_team["matchTeamID"],
                "matchID": match_team["matchID"],
                "userID": match_team["userID"],
                "teamID": match_team["teamID"],
                "matchTeamNum": match_team["matchTeamNum"],
                "realCompetitionID": match_team["realCompetitionID"],
                "realCompetitionMatchDay": match_team["realCompetitionMatchDay"],
                "matchStatus": match_team["matchStatus"],
                "teamName": match_team["teamName"],
                "teamScore": match_team["teamScore"],
                "teamScoreCalc": lineup.score(),
            })
        return results


class GetScoresByMatchIDsAction:
    """Handle MatchTeams GetScoresByMatchIDs requests."""

    @staticmethod
    def execute(db: Session, match_ids: list[int]) -> dict | None:
        return GetScores._execute(db, match_ids=match_ids)


class GetScoresByMatchDayAction:
    """Handle MatchTeams GetScoresByMatchDay requests."""

    @staticmethod
    def execute(
        db: Session,
        competition_type: int,
        competition_match_day: int,
        league_id: int,
        division_id: int | None = None,
    ) -> dict | None:
        return GetScores._execute(
            db,
            competition_type=competition_type,
            competition_match_day=competition_match_day,
            league_id=league_id,
            division_id=division_id,
        )


def _get_match_status(db: Session, match_team: RowMapping, now: datetime) -> int:
    mds = QueryService.get_current_match_day_status(
        db,
        match_day_map_key=match_team["matchDayMapKey"],
        current_datetime=now,
        include_boundaries=True,
    )
    if mds is None:
        return MatchStatusConstants.NOT_STARTED

    if mds["realCompetitionMatchDaySort"] < match_team["realCompetitionMatchDaySort"]:
        return MatchStatusConstants.NOT_STARTED
    elif mds["realCompetitionMatchDaySort"] > match_team["realCompetitionMatchDaySort"]:
        return MatchStatusConstants.FINISHED
    else:
        start_pre = mds["startPreMatch"]
        start_post = mds["startPostMatch"]
        if start_pre is None or start_pre > now:
            return MatchStatusConstants.NOT_STARTED
        elif start_post is not None and start_post < now:
            return MatchStatusConstants.FINISHED
        else:
            return MatchStatusConstants.PLAYING
