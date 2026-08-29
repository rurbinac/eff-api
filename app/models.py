from datetime import datetime

from sqlalchemy import LargeBinary
from sqlalchemy.dialects.mysql import TINYINT
from sqlmodel import Field, SQLModel

from app.utils.dt import UTCDateTime


class User(SQLModel, table=True):
    __tablename__ = "Users"

    userID: int | None = Field(default=None, primary_key=True)
    userEmail: str = Field(max_length=128, unique=True, index=True)
    userPassword: str = Field(max_length=255)
    userName: str = Field(max_length=128)
    userLevel: int = Field(sa_type=TINYINT)
    firstName: str = Field(max_length=50)
    lastName: str = Field(max_length=50)
    birthday: datetime = Field(sa_type=UTCDateTime())
    country: str | None = Field(default=None, max_length=50)
    state: str | None = Field(default=None, max_length=50)
    city: str | None = Field(default=None, max_length=50)
    phoneNumber: str | None = Field(default=None, max_length=15)
    timeZone: str | None = Field(default=None, max_length=20)
    userAvatar: str | None = Field(default=None, max_length=128)
    favoriteTeam: str | None = Field(default=None, max_length=50)
    lastSignInDate: datetime | None = Field(default=None, sa_type=UTCDateTime())
    lastSignInIP: str | None = Field(default=None, max_length=15)
    createdIn: datetime = Field(sa_type=UTCDateTime())
    updatedIn: datetime | None = Field(default=None, sa_type=UTCDateTime())


class RealCompetition(SQLModel, table=True):
    __tablename__ = "RealCompetitions"

    realCompetitionID: int | None = Field(default=None, primary_key=True)
    prevRealCompetitionID: int | None = None
    nextRealCompetitionID: int | None = None
    realCompetitionUID: str = Field(max_length=20)
    realCompetitionSYMID: str = Field(max_length=20)
    realCompetitionName: str = Field(max_length=100)
    realCompetitionCountry: str = Field(max_length=100)
    realCompetitionSeasonId: str = Field(max_length=20)
    realCompetitionSeasonName: str = Field(max_length=100)
    realCompetitionFirstMatchDay: int
    realCompetitionLastMatchDay: int
    realCompetitionExtraMatchDay: int | None = None
    useExtraRealCompetition: int = Field(default=1, sa_type=TINYINT)
    baseRealCompetitionID: int | None = None
    extraRealCompetitionID: int | None = None
    calcStandings: int = Field(sa_type=TINYINT)
    lastF7Date: datetime = Field(default_factory=lambda: datetime(2000, 1, 1), sa_type=UTCDateTime())
    lastF42Date: datetime = Field(default_factory=lambda: datetime(2000, 1, 1), sa_type=UTCDateTime())
    lastFDate: datetime = Field(default_factory=lambda: datetime(2000, 1, 1), sa_type=UTCDateTime())
    createdIn: datetime = Field(sa_type=UTCDateTime())
    updatedIn: datetime | None = Field(default=None, sa_type=UTCDateTime())


class Lookup(SQLModel, table=True):
    __tablename__ = "Lookups"

    lookupID: int | None = Field(default=None, primary_key=True)
    lookupNum: int
    position: int
    lookupKey: str = Field(max_length=20)
    lookupCode: str = Field(max_length=10)
    lookupText: str = Field(max_length=50)


class League(SQLModel, table=True):
    __tablename__ = "Leagues"

    leagueID: int | None = Field(default=None, primary_key=True)
    baseRealCompetitionID: int
    extraRealCompetitionID: int | None = None
    leagueName: str = Field(max_length=128)
    leaguePassword: str = Field(max_length=255)
    commissionerID: int
    prevLeagueID: int | None = None
    nextLeagueID: int | None = None
    season: int
    seasonNum: int
    numDivisions: int
    leagueType: int = Field(sa_type=TINYINT)
    gameType: int = Field(sa_type=TINYINT)
    scoringSystem: int = Field(sa_type=TINYINT)
    tradeDeadline: datetime = Field(sa_type=UTCDateTime())
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
    lowestEPLTeam: int
    lowestGoalkeeper: int
    lowestDefender: int
    lowestMidfielder: int
    lowestStriker: int
    createdBy: int
    createdIn: datetime = Field(sa_type=UTCDateTime())
    updatedBy: int | None = None
    updatedIn: datetime | None = Field(default=None, sa_type=UTCDateTime())


class Division(SQLModel, table=True):
    __tablename__ = "Divisions"

    divisionID: int | None = Field(default=None, primary_key=True)
    baseRealCompetitionID: int
    extraRealCompetitionID: int | None = None
    matchDayMapKey: str | None = Field(default=None, max_length=20)
    leagueID: int
    commissionerID: int
    prevLeagueID: int | None = None
    nextLeagueID: int | None = None
    prevDivisionID: int | None = None
    nextDivisionID: int | None = None
    season: int
    seasonNum: int
    leagueMatches: int = Field(default=0, sa_type=TINYINT)
    divisionMatches: int = Field(default=0, sa_type=TINYINT)
    draftType: str = Field(max_length=1)
    draftDate: datetime = Field(sa_type=UTCDateTime())
    draftCompleteDate: datetime | None = Field(default=None, sa_type=UTCDateTime())
    draftStatus: int
    draftTime: int
    draftingStart: datetime | None = Field(default=None, sa_type=UTCDateTime())
    draftingFinish: datetime | None = Field(default=None, sa_type=UTCDateTime())
    draftingLimit: datetime | None = Field(default=None, sa_type=UTCDateTime())
    draftingRound: int | None = None
    draftingMemberOrder: int | None = None
    draftingTeamOrder: int | None = None
    draftingNextTeamOrder: int | None = None
    draftingUsers: str
    draftingHooks: int = Field(default=0)
    franchiseMembers: str
    firstRealCompetitionMatchDay: int | None = None
    lastRealCompetitionMatchDay: int | None = None
    waiverStatus: int
    matchDay: int | None = None
    isCupMatchDay: int | None = Field(default=None, sa_type=TINYINT)
    isDivisionCupMatchDay: int | None = Field(default=None, sa_type=TINYINT)
    totalTeams: int
    numTeams: int
    availableTeams: int
    divisionType: str = Field(max_length=1)
    createdBy: int
    createdIn: datetime = Field(sa_type=UTCDateTime())
    updatedBy: int | None = None
    updatedIn: datetime | None = Field(default=None, sa_type=UTCDateTime())


class Team(SQLModel, table=True):
    __tablename__ = "Teams"

    teamID: int | None = Field(default=None, primary_key=True)
    baseRealCompetitionID: int
    extraRealCompetitionID: int | None = None
    matchDayMapKey: str | None = Field(default=None, max_length=20)
    leagueID: int
    divisionID: int
    commissionerID: int
    userID: int | None = None
    prevLeagueID: int | None = None
    nextLeagueID: int | None = None
    prevDivisionID: int | None = None
    nextDivisionID: int | None = None
    prevTeamID: int | None = None
    nextTeamID: int | None = None
    season: int
    seasonNum: int
    leagueMatches: int = Field(default=0, sa_type=TINYINT)
    divisionMatches: int = Field(default=0, sa_type=TINYINT)
    draftOrder: int
    randomOrder: int
    waiversOrder: int
    teamName: str = Field(max_length=128)
    teamAvatar: str | None = Field(default=None, max_length=128)
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
    notes: str | None = None
    place: int | None = None
    points: int | None = None
    statusC1: int = Field(default=0, sa_type=TINYINT)
    statusC2: int = Field(default=0, sa_type=TINYINT)
    statusC3: int = Field(default=0, sa_type=TINYINT)
    seedingC1: int = Field(default=0, sa_type=TINYINT)
    seedingC2: int = Field(default=0, sa_type=TINYINT)
    seedingC3: int = Field(default=0, sa_type=TINYINT)
    createdBy: int
    createdIn: datetime = Field(sa_type=UTCDateTime())
    updatedBy: int | None = None
    updatedIn: datetime | None = Field(default=None, sa_type=UTCDateTime())


class MatchDaysMap(SQLModel, table=True):
    __tablename__ = "MatchDaysMap"

    matchDayMapID: int | None = Field(default=None, primary_key=True)
    baseRealCompetitionID: int | None = None
    extraRealCompetitionID: int | None = None
    competitionType: int = Field(sa_type=TINYINT)
    minNumTeams: int
    maxNumTeams: int
    totalMatchDays: int
    rounds: int
    firstRealCompetitionMatchDay: int
    firstRealCompetitionMatchDaySort: int | None = None
    matchDay: int
    realCompetitionID: int | None = None
    realCompetitionSYMID: str = Field(max_length=20)
    realCompetitionSeasonId: str = Field(max_length=20)
    realCompetitionMatchDay: int
    realCompetitionMatchDaySort: int | None = None
    createdBy: int
    createdIn: datetime = Field(sa_type=UTCDateTime())
    updatedBy: int | None = None
    updatedIn: datetime | None = Field(default=None, sa_type=UTCDateTime())


class DivisionNotes(SQLModel, table=True):
    __tablename__ = "DivisionNotes"

    divisionNoteID: int | None = Field(default=None, primary_key=True)
    leagueID: int
    divisionID: int
    teamID: int
    userID: int
    commissionerID: int
    parentDivisionNoteID: int | None = None
    userName: str
    title: str
    notes: str | None = None
    divisionNoteType: str
    createdBy: int
    createdIn: datetime = Field(sa_type=UTCDateTime())
    updatedBy: int | None = None
    updatedIn: datetime | None = Field(default=None, sa_type=UTCDateTime())


class MatchDaysStatus(SQLModel, table=True):
    __tablename__ = "MatchDaysStatus"

    matchDayStatusID: int | None = Field(default=None, primary_key=True)
    baseRealCompetitionID: int | None = None
    extraRealCompetitionID: int | None = None
    matchDayMapKey: str | None = Field(default=None, max_length=20)
    realCompetitionID: int | None = None
    realCompetitionSYMID: str = Field(max_length=20)
    realCompetitionSeasonId: str = Field(max_length=20)
    realCompetitionMatchDay: int
    realCompetitionMatchDaySort: int
    prevActiveMatchDayStatusID: int | None = None
    prevActiveRealCompetitionID: int | None = None
    prevActiveRealCompetitionSYMID: str | None = Field(default=None, max_length=20)
    prevActiveRealCompetitionSeasonId: str | None = Field(default=None, max_length=20)
    prevActiveRealCompetitionMatchDay: int | None = None
    nextActiveMatchDayStatusID: int | None = None
    nextActiveRealCompetitionID: int | None = None
    nextActiveRealCompetitionSYMID: str | None = Field(default=None, max_length=20)
    nextActiveRealCompetitionSeasonId: str | None = Field(default=None, max_length=20)
    nextActiveRealCompetitionMatchDay: int | None = None
    scriptsStatus: str | None = Field(default=None, max_length=20)
    active: int = Field(sa_type=TINYINT)
    locked: int = Field(default=0, sa_type=TINYINT)
    overlapped: int = Field(default=0, sa_type=TINYINT)
    minAllowedRealMatchDate: datetime | None = Field(default=None, sa_type=UTCDateTime())
    maxAllowedRealMatchDate: datetime | None = Field(default=None, sa_type=UTCDateTime())
    minRealMatchDate: datetime | None = Field(default=None, sa_type=UTCDateTime())
    maxRealMatchDate: datetime | None = Field(default=None, sa_type=UTCDateTime())
    startWaivers: datetime | None = Field(default=None, sa_type=UTCDateTime())
    finishWaivers: datetime | None = Field(default=None, sa_type=UTCDateTime())
    startWaiversSettle: datetime | None = Field(default=None, sa_type=UTCDateTime())
    finishWaiversSettle: datetime | None = Field(default=None, sa_type=UTCDateTime())
    startOpenWaivers: datetime | None = Field(default=None, sa_type=UTCDateTime())
    finishOpenWaivers: datetime | None = Field(default=None, sa_type=UTCDateTime())
    startOpenWaiversSettle: datetime | None = Field(default=None, sa_type=UTCDateTime())
    finishOpenWaiversSettle: datetime | None = Field(default=None, sa_type=UTCDateTime())
    startPreMatch: datetime | None = Field(default=None, sa_type=UTCDateTime())
    finishPreMatch: datetime | None = Field(default=None, sa_type=UTCDateTime())
    startMatch: datetime | None = Field(default=None, sa_type=UTCDateTime())
    finishMatch: datetime | None = Field(default=None, sa_type=UTCDateTime())
    startPostMatch: datetime | None = Field(default=None, sa_type=UTCDateTime())
    finishPostMatch: datetime | None = Field(default=None, sa_type=UTCDateTime())
    startMatchDay: datetime | None = Field(default=None, sa_type=UTCDateTime())
    finishMatchDay: datetime | None = Field(default=None, sa_type=UTCDateTime())
    finishBaseMatchDay: datetime | None = Field(default=None, sa_type=UTCDateTime())


class RealStanding(SQLModel, table=True):
    __tablename__ = "RealStandings"

    realStandingID: int | None = Field(default=None, primary_key=True)
    realTeamMemberID: int
    realTeamMemberKey: str = Field(max_length=10)
    prevRealTeamMemberKey: str | None = Field(default=None, max_length=10)
    nextRealTeamMemberKey: str | None = Field(default=None, max_length=10)
    realCompetitionID: int
    realCompetitionUID: str = Field(max_length=20)
    realCompetitionSYMID: str = Field(max_length=20)
    realCompetitionSeasonId: str = Field(max_length=20)
    realCompetitionMatchDay: int
    realCompetitionLastMatchDay: int | None = None
    baseRealCompetitionID: int | None = None
    extraRealCompetitionID: int | None = None
    isTeam: int = Field(sa_type=TINYINT)
    isPlayer: int = Field(sa_type=TINYINT)
    baseMatchDay: int | None = None
    realMatchID: int | None = None
    realMatchTeamID: int | None = None
    realMatchDate: datetime | None = Field(default=None, sa_type=UTCDateTime())
    realMatchTime: int | None = None
    realMatchStatus: int | None = Field(default=None, sa_type=TINYINT)
    realTeamID: int | None = None
    realTeamUID: str | None = Field(default=None, max_length=20)
    realTeamName: str | None = Field(default=None, max_length=128)
    realTeamShortName: str | None = Field(default=None, max_length=10)
    realTeamScore: int | None = None
    realTeamSide: str | None = Field(default=None, max_length=20)
    oppositeRealTeamID: int | None = None
    oppositeRealTeamUID: str | None = Field(default=None, max_length=20)
    oppositeRealTeamName: str | None = Field(default=None, max_length=128)
    oppositeRealTeamShortName: str | None = Field(default=None, max_length=10)
    oppositeRealTeamScore: int | None = None
    realPlayerID: int | None = None
    realPlayerUID: str | None = Field(default=None, max_length=20)
    firstName: str | None = Field(default=None, max_length=100)
    lastName: str | None = Field(default=None, max_length=100)
    knownName: str | None = Field(default=None, max_length=100)
    name: str | None = Field(default=None, max_length=100)
    sortName: str | None = Field(default=None, max_length=100)
    position: str | None = Field(default=None, max_length=20)
    draftPosition: str | None = Field(default=None, max_length=20)
    draftPositionOrder: int | None = Field(default=None, sa_type=TINYINT)
    timePlayed: int | None = None
    gamePlayed: int | None = None
    goals: int | None = None
    assists: int | None = None
    yellowCards: int | None = None
    redCards: int | None = None
    goalsConceded: int | None = None
    cleanSheet: int | None = None
    matchTimePlayed: int | None = None
    matchGamePlayed: int | None = None
    matchGoals: int | None = None
    matchAssists: int | None = None
    matchYellowCards: int | None = None
    matchRedCards: int | None = None
    matchGoalsConceded: int | None = None
    matchCleanSheet: int | None = None
    matchDayPlayed: int | None = None
    matchWon: int | None = None
    matchDraw: int | None = None
    matchLost: int | None = None
    played: int | None = None
    won: int | None = None
    draw: int | None = None
    lost: int | None = None
    goalsFor: int | None = None
    goalsAgainst: int | None = None
    place: int | None = None
    playedHome: int | None = None
    wonHome: int | None = None
    drawHome: int | None = None
    lostHome: int | None = None
    goalsForHome: int | None = None
    goalsAgainstHome: int | None = None
    placeHome: int | None = None
    playedAway: int | None = None
    wonAway: int | None = None
    drawAway: int | None = None
    lostAway: int | None = None
    goalsForAway: int | None = None
    goalsAgainstAway: int | None = None
    placeAway: int | None = None
    matchPointsL1Played: float | None = None
    matchPointsL1GoalsAllowed: float | None = None
    matchPointsL1CleanSheet: float | None = None
    matchPointsL1Cards: float | None = None
    matchPointsL1Goals: float | None = None
    matchPointsL1Assists: float | None = None
    matchPointsL1OwnGoals: float | None = None
    matchPointsL1: float | None = None
    pointsL1Played: float | None = None
    pointsL1GoalsAllowed: float | None = None
    pointsL1CleanSheet: float | None = None
    pointsL1Cards: float | None = None
    pointsL1Goals: float | None = None
    pointsL1Assists: float | None = None
    pointsL1OwnGoals: float | None = None
    pointsL1: float | None = None
    livePointsL1: float | None = None
    ranking: int | None = None
    processed: int = Field(sa_type=TINYINT)
    createdIn: datetime = Field(sa_type=UTCDateTime())
    updatedIn: datetime | None = Field(default=None, sa_type=UTCDateTime())


class MatchTeam(SQLModel, table=True):
    __tablename__ = "MatchTeams"

    matchTeamID: int | None = Field(default=None, primary_key=True)
    matchID: int
    matchTeamNum: int = Field(sa_type=TINYINT)
    userID: int | None = None
    teamID: int | None = None
    teamName: str | None = Field(default=None, max_length=128)
    teamScore: float | None = None
    teamPoints: int | None = None
    teamSeeding: int | None = Field(default=None, sa_type=TINYINT)
    matchDayMapKey: str | None = Field(default=None, max_length=20)
    lineup: str | None = Field(default=None, max_length=240)
    cntEPLTeam: int | None = Field(default=None, sa_type=TINYINT)
    cntGoalkeeper: int | None = Field(default=None, sa_type=TINYINT)
    cntDefender: int | None = Field(default=None, sa_type=TINYINT)
    cntMidfielder: int | None = Field(default=None, sa_type=TINYINT)
    cntStriker: int | None = Field(default=None, sa_type=TINYINT)
    cntSubstitute: int | None = Field(default=None, sa_type=TINYINT)
    cntInactive: int | None = Field(default=None, sa_type=TINYINT)
    place: int | None = None
    won: int | None = None
    draw: int | None = None
    lost: int | None = None
    scoreFor: float | None = None
    scoreAgainst: float | None = None
    points: int | None = None
    wonHome: int | None = None
    drawHome: int | None = None
    lostHome: int | None = None
    scoreForHome: float | None = None
    scoreAgainstHome: float | None = None
    pointsHome: int | None = None
    wonAway: int | None = None
    drawAway: int | None = None
    lostAway: int | None = None
    scoreForAway: float | None = None
    scoreAgainstAway: float | None = None
    pointsAway: int | None = None
    createdBy: int | None = None
    createdIn: datetime = Field(sa_type=UTCDateTime())
    updatedBy: int | None = None
    updatedIn: datetime | None = Field(default=None, sa_type=UTCDateTime())


class Match(SQLModel, table=True):
    __tablename__ = "Matches"

    matchID: int | None = Field(default=None, primary_key=True)
    matchStatus: int = Field(sa_type=TINYINT)
    leagueID: int
    divisionID: int
    season: int
    seasonNum: int
    realCompetitionID: int | None = None
    realCompetitionMatchDay: int | None = None
    realCompetitionMatchDaySort: int | None = None
    competitionType: int = Field(sa_type=TINYINT)
    competitionMatchDay: int | None = None
    competitionLastMatchDay: int | None = None
    competitionMatchNumber: int | None = None
    competitionMatchGroup: int | None = None
    competitionMatchNextGroup: int | None = None
    competitionMatchRound: int | None = None
    competitionMatchLastRound: int | None = None
    matchGroupWinnerTeamID: int | None = None
    lastCompetitionMatchDay: int | None = None
    createdBy: int | None = None
    createdIn: datetime = Field(sa_type=UTCDateTime())
    updatedBy: int | None = None
    updatedIn: datetime | None = Field(default=None, sa_type=UTCDateTime())


class RealMatch(SQLModel, table=True):
    __tablename__ = "RealMatches"

    realMatchID: int | None = Field(default=None, primary_key=True)
    realMatchStatus: int = Field(sa_type=TINYINT)
    realMatchType: str = Field(max_length=20)
    realMatchPeriod: str | None = Field(default=None, max_length=20)
    realMatchRealPeriod: str | None = Field(default=None, max_length=20)
    realMatchAttendance: int | None = None
    realMatchDate: datetime = Field(sa_type=UTCDateTime())
    realMatchDateOffset: int | None = None
    realMatchResultType: str | None = Field(default=None, max_length=20)
    realMatchTime: int | None = None
    realMatchFirstHalfTime: int | None = None
    realMatchSecondHalfTime: int | None = None
    realMatchFirstHalfExtraTime: int | None = None
    realMatchSecondHalfExtraTime: int | None = None
    realMatchEnded: int = Field(sa_type=TINYINT)
    realMatchIgnore: int = Field(sa_type=TINYINT)
    realCompetitionID: int
    realCompetitionUID: str = Field(max_length=20)
    realCompetitionSYMID: str = Field(max_length=20)
    realCompetitionSeasonId: str = Field(max_length=20)
    realCompetitionMatchDay: int
    realCompetitionFirstMatchDay: int | None = None
    realCompetitionLastMatchDay: int | None = None
    baseRealCompetitionID: int | None = None
    extraRealCompetitionID: int | None = None
    realVenueID: int | None = None
    realVenueUID: str | None = Field(default=None, max_length=20)
    firstRealTeamMemberID: int | None = None
    firstRealTeamMemberKey: str | None = Field(default=None, max_length=10)
    firstRealTeamID: int | None = None
    firstRealTeamUID: str | None = Field(default=None, max_length=20)
    firstRealTeamName: str | None = Field(default=None, max_length=128)
    firstRealTeamShortName: str | None = Field(default=None, max_length=10)
    firstRealTeamScore: int | None = None
    firstRealTeamRealScore: int | None = None
    firstRealTeamSide: str | None = Field(default=None, max_length=20)
    firstRealTeamCleanSheet: int | None = Field(default=None, sa_type=TINYINT)
    firstRealTeamResult: int | None = Field(default=None, sa_type=TINYINT)
    firstRealTeamPoints: int | None = Field(default=None, sa_type=TINYINT)
    firstRealTeamNumber: int | None = Field(default=None, sa_type=TINYINT)
    secondRealTeamMemberID: int | None = None
    secondRealTeamMemberKey: str | None = Field(default=None, max_length=10)
    secondRealTeamID: int | None = None
    secondRealTeamUID: str | None = Field(default=None, max_length=20)
    secondRealTeamName: str | None = Field(default=None, max_length=128)
    secondRealTeamShortName: str | None = Field(default=None, max_length=10)
    secondRealTeamScore: int | None = None
    secondRealTeamRealScore: int | None = None
    secondRealTeamSide: str | None = Field(default=None, max_length=20)
    secondRealTeamCleanSheet: int | None = Field(default=None, sa_type=TINYINT)
    secondRealTeamResult: int | None = Field(default=None, sa_type=TINYINT)
    secondRealTeamPoints: int | None = Field(default=None, sa_type=TINYINT)
    secondRealTeamNumber: int | None = Field(default=None, sa_type=TINYINT)
    enabled: int = Field(sa_type=TINYINT)
    lastF7Date: datetime | None = Field(default=None, sa_type=UTCDateTime())
    lastF42Date: datetime | None = Field(default=None, sa_type=UTCDateTime())
    lastFDate: datetime | None = Field(default=None, sa_type=UTCDateTime())
    createdIn: datetime = Field(sa_type=UTCDateTime())
    updatedIn: datetime | None = Field(default=None, sa_type=UTCDateTime())


class RealMatchTeam(SQLModel, table=True):
    __tablename__ = "RealMatchTeams"

    realMatchTeamID: int | None = Field(default=None, primary_key=True)
    realMatchID: int
    realTeamMemberID: int | None = None
    realTeamMemberKey: str | None = Field(default=None, max_length=10)
    realTeamID: int
    realTeamUID: str = Field(max_length=20)
    realTeamName: str = Field(max_length=128)
    realTeamShortName: str | None = Field(default=None, max_length=10)
    realTeamScore: int | None = None
    realTeamRealScore: int | None = None
    realTeamSide: str = Field(max_length=20)
    realTeamCleanSheet: int | None = Field(default=None, sa_type=TINYINT)
    realTeamResult: int | None = Field(default=None, sa_type=TINYINT)
    realTeamPoints: int | None = Field(default=None, sa_type=TINYINT)
    realTeamNumber: int = Field(sa_type=TINYINT)
    pointsL1: float | None = None
    createdIn: datetime = Field(sa_type=UTCDateTime())
    updatedIn: datetime | None = Field(default=None, sa_type=UTCDateTime())


class TeamMemberTransfers(SQLModel, table=True):
    __tablename__ = "TeamMemberTransfers"

    teamMemberTransferID: int | None = Field(default=None, primary_key=True)
    createdIn: datetime = Field(sa_type=UTCDateTime())
    updatedIn: datetime | None = Field(default=None, sa_type=UTCDateTime())


class TeamMemberLog(SQLModel, table=True):
    __tablename__ = "TeamMemberLog"

    teamMemberLogID: int | None = Field(default=None, primary_key=True)
    teamMemberTransferID: int | None = None
    leagueID: int
    divisionID: int
    teamID: int
    userID: int
    requester: int | None = None
    transactionType: int
    membersBefore: str | None = Field(default=None, max_length=500)
    membersAfter: str | None = Field(default=None, max_length=500)
    createdIn: datetime = Field(sa_type=UTCDateTime())
    updatedIn: datetime | None = Field(default=None, sa_type=UTCDateTime())


class Feed(SQLModel, table=True):
    __tablename__ = "Feeds"

    feedID: int | None = Field(default=None, primary_key=True)
    feedName: str | None = Field(default=None, max_length=128)
    feedType: str = Field(max_length=4)
    versions: int = Field(default=1)
    startDate: datetime = Field(sa_type=UTCDateTime())
    endDate: datetime | None = Field(default=None, sa_type=UTCDateTime())
    duration: float | None = None
    size: int = Field(default=0)
    totalSize: int = Field(default=0)
    sha256: bytes | None = Field(default=None, sa_type=LargeBinary(32))
    compressedName: str | None = Field(default=None, max_length=128)
    createdIn: datetime = Field(default_factory=datetime.utcnow, sa_type=UTCDateTime())
    updatedIn: datetime | None = Field(default=None, sa_type=UTCDateTime())
