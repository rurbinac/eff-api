from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy.dialects.mysql import TINYINT


class User(SQLModel, table=True):
    __tablename__ = "Users"

    userID: Optional[int] = Field(default=None, primary_key=True)
    userEmail: str = Field(max_length=128, unique=True, index=True)
    userPassword: str = Field(max_length=255)
    userName: str = Field(max_length=128)
    userLevel: int = Field(sa_type=TINYINT)
    firstName: str = Field(max_length=50)
    lastName: str = Field(max_length=50)
    birthday: datetime
    country: Optional[str] = Field(default=None, max_length=50)
    state: Optional[str] = Field(default=None, max_length=50)
    city: Optional[str] = Field(default=None, max_length=50)
    phoneNumber: Optional[str] = Field(default=None, max_length=15)
    timeZone: Optional[str] = Field(default=None, max_length=20)
    userAvatar: Optional[str] = Field(default=None, max_length=128)
    favoriteTeam: Optional[str] = Field(default=None, max_length=50)
    lastSignInDate: Optional[datetime] = Field(default=None)
    lastSignInIP: Optional[str] = Field(default=None, max_length=15)
    createdIn: datetime
    updatedIn: Optional[datetime] = Field(default=None)


class RealCompetition(SQLModel, table=True):
    __tablename__ = "RealCompetitions"

    realCompetitionID: Optional[int] = Field(default=None, primary_key=True)
    prevRealCompetitionID: Optional[int] = None
    nextRealCompetitionID: Optional[int] = None
    realCompetitionUID: str = Field(max_length=20)
    realCompetitionSYMID: str = Field(max_length=20)
    realCompetitionName: str = Field(max_length=100)
    realCompetitionCountry: str = Field(max_length=100)
    realCompetitionSeasonId: str = Field(max_length=20)
    realCompetitionSeasonName: str = Field(max_length=100)
    realCompetitionFirstMatchDay: int
    realCompetitionLastMatchDay: int
    realCompetitionExtraMatchDay: Optional[int] = None
    useExtraRealCompetition: int = Field(default=1, sa_type=TINYINT)
    baseRealCompetitionID: Optional[int] = None
    extraRealCompetitionID: Optional[int] = None
    calcStandings: int = Field(sa_type=TINYINT)
    lastF7Date: datetime = Field(default_factory=lambda: datetime(2000, 1, 1))
    lastF42Date: datetime = Field(default_factory=lambda: datetime(2000, 1, 1))
    lastFDate: datetime = Field(default_factory=lambda: datetime(2000, 1, 1))
    createdIn: datetime
    updatedIn: Optional[datetime] = None


class Lookup(SQLModel, table=True):
    __tablename__ = "Lookups"

    lookupID: Optional[int] = Field(default=None, primary_key=True)
    lookupNum: int
    position: int
    lookupKey: str = Field(max_length=20)
    lookupCode: str = Field(max_length=10)
    lookupText: str = Field(max_length=50)


class League(SQLModel, table=True):
    __tablename__ = "Leagues"

    leagueID: Optional[int] = Field(default=None, primary_key=True)
    baseRealCompetitionID: int
    extraRealCompetitionID: Optional[int] = None
    leagueName: str = Field(max_length=128)
    leaguePassword: str = Field(max_length=255)
    commissionerID: int
    prevLeagueID: Optional[int] = None
    nextLeagueID: Optional[int] = None
    season: int
    seasonNum: int
    numDivisions: int
    leagueType: int = Field(sa_type=TINYINT)
    gameType: int = Field(sa_type=TINYINT)
    scoringSystem: int = Field(sa_type=TINYINT)
    tradeDeadline: datetime
    publishLeague: int = Field(sa_type=TINYINT)
    seasonStatus: int
    totalTeams: int
    availableTeams: int
    totPromoted: int = Field(default=2, sa_type=TINYINT)
    maxFranchiseMembers: int = Field(default=2, sa_type=TINYINT)
    maxWaiver: int
    minEPLTeam: int
    minPlayer: int
    minGoalkeeper: int
    minDefender: int
    minMidfielder: int
    minStriker: int
    maxEPLTeam: int
    maxPlayer: int
    maxGoalkeeper: int
    maxDefender: int
    maxMidfielder: int
    maxStriker: int
    autoEPLTeam: int
    autoGoalkeeper: int
    autoDefender: int
    autoMidfielder: int
    autoStriker: int
    createdBy: int
    createdIn: datetime
    updatedBy: Optional[int] = None
    updatedIn: Optional[datetime] = None


class Division(SQLModel, table=True):
    __tablename__ = "Divisions"

    divisionID: Optional[int] = Field(default=None, primary_key=True)
    baseRealCompetitionID: int
    extraRealCompetitionID: Optional[int] = None
    matchDayMapKey: Optional[str] = Field(default=None, max_length=20)
    leagueID: int
    commissionerID: int
    prevLeagueID: Optional[int] = None
    nextLeagueID: Optional[int] = None
    prevDivisionID: Optional[int] = None
    nextDivisionID: Optional[int] = None
    season: int
    seasonNum: int
    leagueMatches: int = Field(default=0, sa_type=TINYINT)
    divisionMatches: int = Field(default=0, sa_type=TINYINT)
    draftType: str = Field(max_length=1)
    draftDate: datetime
    draftCompleteDate: Optional[datetime] = None
    draftStatus: int
    draftTime: int
    draftingStart: Optional[datetime] = None
    draftingFinish: Optional[datetime] = None
    draftingLimit: Optional[datetime] = None
    draftingRound: Optional[int] = None
    draftingMemberOrder: Optional[int] = None
    draftingTeamOrder: Optional[int] = None
    draftingNextTeamOrder: Optional[int] = None
    draftingUsers: str
    draftingHooks: int = Field(default=0)
    franchiseMembers: str
    firstRealCompetitionMatchDay: Optional[int] = None
    lastRealCompetitionMatchDay: Optional[int] = None
    waiverStatus: int
    matchDay: Optional[int] = None
    isCupMatchDay: Optional[int] = Field(default=None, sa_type=TINYINT)
    isDivisionCupMatchDay: Optional[int] = Field(default=None, sa_type=TINYINT)
    totalTeams: int
    numTeams: int
    availableTeams: int
    divisionType: str = Field(max_length=1)
    createdBy: int
    createdIn: datetime
    updatedBy: Optional[int] = None
    updatedIn: Optional[datetime] = None


class Team(SQLModel, table=True):
    __tablename__ = "Teams"

    teamID: Optional[int] = Field(default=None, primary_key=True)
    baseRealCompetitionID: int
    extraRealCompetitionID: Optional[int] = None
    matchDayMapKey: Optional[str] = Field(default=None, max_length=20)
    leagueID: int
    divisionID: int
    commissionerID: int
    userID: Optional[int] = None
    prevLeagueID: Optional[int] = None
    nextLeagueID: Optional[int] = None
    prevDivisionID: Optional[int] = None
    nextDivisionID: Optional[int] = None
    prevTeamID: Optional[int] = None
    nextTeamID: Optional[int] = None
    season: int
    seasonNum: int
    leagueMatches: int = Field(default=0, sa_type=TINYINT)
    divisionMatches: int = Field(default=0, sa_type=TINYINT)
    draftOrder: int
    randomOrder: int
    waiversOrder: int
    teamName: str = Field(max_length=128)
    teamAvatar: Optional[str] = Field(default=None, max_length=128)
    teamMembers: str
    draftMembers: str
    membersRanking: str
    membersWaivers: str
    membersWishList: str
    franchiseWishList: str
    fantasyPoints: int
    teamRanking: int
    locked: int = Field(sa_type=TINYINT)
    isCommissioner: int = Field(sa_type=TINYINT)
    cntEPLTeam: int
    cntPlayer: int
    cntGoalkeeper: int
    cntDefender: int
    cntMidfielder: int
    cntStriker: int
    cntAdd: int
    cntDrop: int
    cntWaiver: int
    notes: Optional[str] = None
    place: Optional[int] = None
    points: Optional[int] = None
    statusC1: int = Field(default=0, sa_type=TINYINT)
    statusC2: int = Field(default=0, sa_type=TINYINT)
    statusC3: int = Field(default=0, sa_type=TINYINT)
    seedingC1: int = Field(default=0, sa_type=TINYINT)
    seedingC2: int = Field(default=0, sa_type=TINYINT)
    seedingC3: int = Field(default=0, sa_type=TINYINT)
    createdBy: int
    createdIn: datetime
    updatedBy: Optional[int] = None
    updatedIn: Optional[datetime] = None


class MatchDaysMap(SQLModel, table=True):
    __tablename__ = "MatchDaysMap"

    matchDayMapID: Optional[int] = Field(default=None, primary_key=True)
    baseRealCompetitionID: Optional[int] = None
    extraRealCompetitionID: Optional[int] = None
    competitionType: int = Field(sa_type=TINYINT)
    minNumTeams: int
    maxNumTeams: int
    totalMatchDays: int
    rounds: int
    firstRealCompetitionMatchDay: int
    firstRealCompetitionMatchDaySort: Optional[int] = None
    matchDay: int
    realCompetitionID: Optional[int] = None
    realCompetitionSYMID: str = Field(max_length=20)
    realCompetitionSeasonId: str = Field(max_length=20)
    realCompetitionMatchDay: int
    realCompetitionMatchDaySort: Optional[int] = None
    createdBy: int
    createdIn: datetime
    updatedBy: Optional[int] = None
    updatedIn: Optional[datetime] = None


class MatchDaysStatus(SQLModel, table=True):
    __tablename__ = "MatchDaysStatus"

    matchDayStatusID: Optional[int] = Field(default=None, primary_key=True)
    baseRealCompetitionID: Optional[int] = None
    extraRealCompetitionID: Optional[int] = None
    matchDayMapKey: Optional[str] = Field(default=None, max_length=20)
    realCompetitionID: Optional[int] = None
    realCompetitionSYMID: str = Field(max_length=20)
    realCompetitionSeasonId: str = Field(max_length=20)
    realCompetitionMatchDay: int
    realCompetitionMatchDaySort: int
    prevActiveMatchDayStatusID: Optional[int] = None
    prevActiveRealCompetitionID: Optional[int] = None
    prevActiveRealCompetitionSYMID: Optional[str] = Field(default=None, max_length=20)
    prevActiveRealCompetitionSeasonId: Optional[str] = Field(default=None, max_length=20)
    prevActiveRealCompetitionMatchDay: Optional[int] = None
    nextActiveMatchDayStatusID: Optional[int] = None
    nextActiveRealCompetitionID: Optional[int] = None
    nextActiveRealCompetitionSYMID: Optional[str] = Field(default=None, max_length=20)
    nextActiveRealCompetitionSeasonId: Optional[str] = Field(default=None, max_length=20)
    nextActiveRealCompetitionMatchDay: Optional[int] = None
    scriptsStatus: Optional[str] = Field(default=None, max_length=20)
    active: int = Field(sa_type=TINYINT)
    locked: int = Field(default=0, sa_type=TINYINT)
    overlapped: int = Field(default=0, sa_type=TINYINT)
    minAllowedRealMatchDate: Optional[datetime] = None
    maxAllowedRealMatchDate: Optional[datetime] = None
    minRealMatchDate: Optional[datetime] = None
    maxRealMatchDate: Optional[datetime] = None
    startWaivers: Optional[datetime] = None
    finishWaivers: Optional[datetime] = None
    startWaiversSettle: Optional[datetime] = None
    finishWaiversSettle: Optional[datetime] = None
    startOpenWaivers: Optional[datetime] = None
    finishOpenWaivers: Optional[datetime] = None
    startOpenWaiversSettle: Optional[datetime] = None
    finishOpenWaiversSettle: Optional[datetime] = None
    startPreMatch: Optional[datetime] = None
    finishPreMatch: Optional[datetime] = None
    startMatch: Optional[datetime] = None
    finishMatch: Optional[datetime] = None
    startPostMatch: Optional[datetime] = None
    finishPostMatch: Optional[datetime] = None
    startMatchDay: Optional[datetime] = None
    finishMatchDay: Optional[datetime] = None
    finishBaseMatchDay: Optional[datetime] = None
