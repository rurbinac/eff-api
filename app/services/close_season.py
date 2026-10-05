import random
from collections.abc import Iterator
from datetime import datetime

from sqlalchemy import Row, func, select
from sqlalchemy.orm import Session

from app.constants import DraftConstants
from app.models import Division, League, Match, MatchDaysStatus, MatchTeam, Team
from app.services.query import QueryService
from app.utils.dt import utc_now


class CloseSeason:
    def __init__(self, db: Session):
        self._db: Session = db
        self._base_rc_id = None
        self._base_rc_md = None
        self._next_rc = None

    def execute(self, rc_id: int | None = None, now: datetime | None = None):
        if self._get_match_day(rc_id, now):
            for lg in self._read_league():
                self._resort_teams(lg)
                self._create_league(lg)

    def _get_match_day(
        self, rc_id: int | None = None, now: datetime | None = None
    ) -> bool:
        rc = QueryService.get_base_competition(self._db, rc_id)
        if not rc:
            return False
        self._base_rc_id = rc["realCompetitionID"]
        self._next_rc = QueryService.get_base_competition(
            self._db, rc["nextRealCompetitionID"]
        )
        if not self._next_rc:
            return False
        now = utc_now() if now is None else now
        row = self._db.execute(
            select(
                MatchDaysStatus.realCompetitionID,
                MatchDaysStatus.realCompetitionMatchDay,
            )
            .where(
                MatchDaysStatus.baseRealCompetitionID == self._base_rc_id,
                MatchDaysStatus.active == 1,
                MatchDaysStatus.startPostMatch <= now,
                MatchDaysStatus.finishPostMatch > now,
            )
            .distinct()
        ).first()
        if row and row.realCompetitionID == self._base_rc_id:
            self._base_rc_md = row.realCompetitionMatchDay
            return True
        else:
            self._base_rc_md = None
            return False

    def _resort_teams(self, lg: dict) -> None:
        tot = lg["league"].totPromoted
        if tot <= 0:
            return
        divs = list(lg["dv"].values())
        for i in range(len(divs) - 1):
            dv_up = divs[i]
            dv_down = divs[i + 1]
            relegated = dv_up["tm"][-tot:]
            promoted = dv_down["tm"][:tot]
            dv_up["tm"] = dv_up["tm"][:-tot] + promoted
            dv_down["tm"] = relegated + dv_down["tm"][tot:]

    def _create_league(self, lg: dict) -> None:
        now = utc_now()
        old_league = lg["league"]
        next_base_rc_id = self._next_rc["realCompetitionID"]
        next_extra_rc_id = self._next_rc["extraRealCompetitionID"]
        next_season = old_league.season + 1
        next_season_num = old_league.seasonNum + 1
        new_league = League(
            **{
                k: v
                for k, v in old_league.model_dump().items()
                if k
                not in (
                    "leagueID",
                    "baseRealCompetitionID",
                    "extraRealCompetitionID",
                    "prevLeagueID",
                    "nextLeagueID",
                    "season",
                    "seasonNum",
                    "createdIn",
                    "updatedIn",
                    "updatedBy",
                    # TODO: seasonStatus — carries over old season state; reset when status values are defined
                    # TODO: tradeDeadline — copied as past date; update before season activates
                )
            },
            baseRealCompetitionID=next_base_rc_id,
            extraRealCompetitionID=next_extra_rc_id,
            prevLeagueID=old_league.leagueID,
            nextLeagueID=None,
            season=next_season,
            seasonNum=next_season_num,
            createdBy=old_league.commissionerID,
            createdIn=now,
        )
        self._db.add(new_league)
        self._db.flush()
        old_league.nextLeagueID = new_league.leagueID
        total_teams = sum(len(dv["tm"]) for dv in lg["dv"].values())
        seeding_c3 = list(range(1, total_teams + 1))
        random.shuffle(seeding_c3)
        seeding_c3_idx = 0
        for dv in lg["dv"].values():
            old_division = dv["division"]
            new_division = Division(
                **{
                    k: v
                    for k, v in old_division.model_dump().items()
                    if k
                    not in (
                        "divisionID",
                        "leagueID",
                        "baseRealCompetitionID",
                        "extraRealCompetitionID",
                        "prevDivisionID",
                        "nextDivisionID",
                        "prevLeagueID",
                        "nextLeagueID",
                        "season",
                        "seasonNum",
                        "createdIn",
                        "updatedIn",
                        "updatedBy",
                        "draftCompleteDate",
                        "draftingStart",
                        "draftingFinish",
                        "draftingLimit",
                        "draftingRound",
                        "draftingMemberOrder",
                        "draftingTeamOrder",
                        "draftingNextTeamOrder",
                        "matchDay",
                        "waiverStatus",
                        "draftStatus",
                        # TODO: draftDate — copied as past date; update before draft activates
                        "firstRealCompetitionMatchDay",
                        "lastRealCompetitionMatchDay",
                        "matchDayMapKey",
                    )
                },
                baseRealCompetitionID=next_base_rc_id,
                extraRealCompetitionID=next_extra_rc_id,
                leagueID=new_league.leagueID,
                prevLeagueID=old_league.leagueID,
                nextLeagueID=None,
                prevDivisionID=old_division.divisionID,
                nextDivisionID=None,
                season=old_division.season+1,
                seasonNum=old_division.seasonNum+1,
                waiverStatus=0,
                draftStatus=DraftConstants.DRAFT_STATUS_NOT_DRAFTED,
                firstRealCompetitionMatchDay=None,
                lastRealCompetitionMatchDay=None,
                matchDayMapKey=None,
                matchDay=None,
                draftCompleteDate=None,
                draftingStart=None,
                draftingFinish=None,
                draftingLimit=None,
                draftingRound=None,
                draftingMemberOrder=None,
                draftingTeamOrder=None,
                draftingNextTeamOrder=None,
                createdBy=old_league.commissionerID,
                createdIn=now,
            )
            self._db.add(new_division)
            self._db.flush()
            old_division.nextDivisionID = new_division.divisionID
            num_teams = len(dv["tm"])
            for i, old_team in enumerate(dv["tm"]):
                new_team = Team(
                    baseRealCompetitionID=next_base_rc_id,
                    extraRealCompetitionID=next_extra_rc_id,
                    leagueID=new_league.leagueID,
                    divisionID=new_division.divisionID,
                    commissionerID=old_team.commissionerID,
                    userID=old_team.userID,
                    prevLeagueID=old_league.leagueID,
                    nextLeagueID=None,
                    prevDivisionID=old_team.divisionID,
                    nextDivisionID=None,
                    prevTeamID=old_team.teamID,
                    nextTeamID=None,
                    season=old_team.season+1,
                    seasonNum=old_team.seasonNum+1,
                    leagueMatches=0,
                    divisionMatches=0,
                    draftOrder=0,
                    randomOrder=0,
                    waiversOrder=num_teams-i,
                    teamName=old_team.teamName,
                    teamAvatar=old_team.teamAvatar,
                    teamMembers="",
                    draftMembers="",
                    membersRanking="",
                    membersWaivers="",
                    membersWishList="",
                    franchiseWishList="",
                    fantasyPoints=0,
                    teamRanking=0,
                    locked=0,
                    isCommissioner=old_team.isCommissioner,
                    cntEPLTeam=0,
                    cntPlayer=0,
                    cntGoalkeeper=0,
                    cntDefender=0,
                    cntMidfielder=0,
                    cntStriker=0,
                    cntAdd=0,
                    cntDrop=0,
                    cntWaiver=0,
                    matchDayMapKey=None,
                    place=None,
                    points=None,
                    statusC1=0,
                    statusC2=0,
                    statusC3=0,
                    seedingC1=i+1,
                    seedingC2=i+1,
                    seedingC3=seeding_c3[seeding_c3_idx],
                    createdBy=old_league.commissionerID,
                    createdIn=now,
                )
                self._db.add(new_team)
                self._db.flush()
                old_team.nextTeamID = new_team.teamID
                old_team.nextDivisionID = new_division.divisionID
                seeding_c3_idx += 1
        self._db.commit()

    def _read_league(self) -> Iterator[dict]:
        lg = None
        for row in self._read_row():
            if lg is None or row.League.leagueID != lg["league"].leagueID:
                if lg is not None:
                    yield lg
                lg = {"league": row.League, "dv": {}}
            dv_id = row.Division.divisionID
            if dv_id not in lg["dv"]:
                lg["dv"][dv_id] = {"division": row.Division, "tm": []}
            lg["dv"][dv_id]["tm"].append(row.Team)
        if lg is not None:
            yield lg

    def _read_row(self) -> Iterator[Row]:
        subq = (
            select(Team.leagueID)
            .join(MatchTeam, MatchTeam.teamID == Team.teamID)
            .join(Match, Match.matchID == MatchTeam.matchID)
            .where(Match.realCompetitionID == self._base_rc_id)
            .group_by(Team.leagueID)
            .having(func.max(Match.realCompetitionMatchDay) == self._base_rc_md)
            .scalar_subquery()
        )
        yield from self._db.execute(
            select(League, Division, Team)
            .join(Division, Division.leagueID == League.leagueID)
            .join(Team, Team.divisionID == Division.divisionID)
            .where(League.leagueID.in_(subq))
            .order_by(League.leagueID, Division.divisionID, Team.waiversOrder.desc())
        )
