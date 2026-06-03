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


class DivisionNotes(SQLModel, table=True):
    __tablename__ = "DivisionNotes"

    divisionNoteID: Optional[int] = Field(default=None, primary_key=True)
    leagueID: int
    divisionID: int
    teamID: int
    userID: int
    commissionerID: int
    parentDivisionNoteID: Optional[int] = None
    userName: str
    title: str
    notes: Optional[str] = None
    divisionNoteType: str
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


class TeamStanding(SQLModel, table=True):
    __tablename__ = "TeamStandings"

    teamStandingID: Optional[int] = Field(default=None, primary_key=True)
    leagueID: int
    divisionID: int
    teamID: int
    userID: int
    season: int
    seasonNum: int
    matchDayMapKey: Optional[str] = Field(default=None, max_length=20)
    realCompetitionID: Optional[int] = None
    realCompetitionMatchDay: Optional[int] = None
    competitionMatchDay: Optional[int] = None
    lastCompetitionMatchDay: Optional[int] = None
    teamName: str = Field(max_length=128)
    place: Optional[int] = None
    won: Optional[int] = None
    draw: Optional[int] = None
    lost: Optional[int] = None
    scoreFor: Optional[float] = None
    scoreAgainst: Optional[float] = None
    points: Optional[int] = None
    wonHome: Optional[int] = None
    drawHome: Optional[int] = None
    lostHome: Optional[int] = None
    scoreForHome: Optional[float] = None
    scoreAgainstHome: Optional[float] = None
    pointsHome: Optional[int] = None
    wonAway: Optional[int] = None
    drawAway: Optional[int] = None
    lostAway: Optional[int] = None
    scoreForAway: Optional[float] = None
    scoreAgainstAway: Optional[float] = None
    pointsAway: Optional[int] = None
    createdBy: Optional[int] = None
    createdIn: datetime
    updatedBy: Optional[int] = None
    updatedIn: Optional[datetime] = None


class RealStanding(SQLModel, table=True):
    __tablename__ = "RealStandings"

    realStandingID: Optional[int] = Field(default=None, primary_key=True)
    realTeamMemberID: int
    realTeamMemberKey: str = Field(max_length=10)
    prevRealTeamMemberKey: Optional[str] = Field(default=None, max_length=10)
    nextRealTeamMemberKey: Optional[str] = Field(default=None, max_length=10)
    realCompetitionID: int
    realCompetitionUID: str = Field(max_length=20)
    realCompetitionSYMID: str = Field(max_length=20)
    realCompetitionSeasonId: str = Field(max_length=20)
    realCompetitionMatchDay: int
    realCompetitionLastMatchDay: Optional[int] = None
    baseRealCompetitionID: Optional[int] = None
    extraRealCompetitionID: Optional[int] = None
    isTeam: int = Field(sa_type=TINYINT)
    isPlayer: int = Field(sa_type=TINYINT)
    baseMatchDay: Optional[int] = None
    realMatchID: Optional[int] = None
    realMatchTeamID: Optional[int] = None
    realMatchDate: Optional[datetime] = None
    realMatchTime: Optional[int] = None
    realMatchStatus: Optional[int] = Field(default=None, sa_type=TINYINT)
    realTeamID: Optional[int] = None
    realTeamUID: Optional[str] = Field(default=None, max_length=20)
    realTeamName: Optional[str] = Field(default=None, max_length=128)
    realTeamShortName: Optional[str] = Field(default=None, max_length=10)
    realTeamScore: Optional[int] = None
    realTeamSide: Optional[str] = Field(default=None, max_length=20)
    oppositeRealTeamID: Optional[int] = None
    oppositeRealTeamUID: Optional[str] = Field(default=None, max_length=20)
    oppositeRealTeamName: Optional[str] = Field(default=None, max_length=128)
    oppositeRealTeamShortName: Optional[str] = Field(default=None, max_length=10)
    oppositeRealTeamScore: Optional[int] = None
    realPlayerID: Optional[int] = None
    realPlayerUID: Optional[str] = Field(default=None, max_length=20)
    firstName: Optional[str] = Field(default=None, max_length=100)
    lastName: Optional[str] = Field(default=None, max_length=100)
    knownName: Optional[str] = Field(default=None, max_length=100)
    name: Optional[str] = Field(default=None, max_length=100)
    sortName: Optional[str] = Field(default=None, max_length=100)
    position: Optional[str] = Field(default=None, max_length=20)
    draftPosition: Optional[str] = Field(default=None, max_length=20)
    draftPositionOrder: Optional[int] = Field(default=None, sa_type=TINYINT)
    timePlayed: Optional[int] = None
    gamePlayed: Optional[int] = None
    goals: Optional[int] = None
    assists: Optional[int] = None
    yellowCards: Optional[int] = None
    redCards: Optional[int] = None
    goalsConceded: Optional[int] = None
    cleanSheet: Optional[int] = None
    matchTimePlayed: Optional[int] = None
    matchGamePlayed: Optional[int] = None
    matchGoals: Optional[int] = None
    matchAssists: Optional[int] = None
    matchYellowCards: Optional[int] = None
    matchRedCards: Optional[int] = None
    matchGoalsConceded: Optional[int] = None
    matchCleanSheet: Optional[int] = None
    matchDayPlayed: Optional[int] = None
    matchWon: Optional[int] = None
    matchDraw: Optional[int] = None
    matchLost: Optional[int] = None
    played: Optional[int] = None
    won: Optional[int] = None
    draw: Optional[int] = None
    lost: Optional[int] = None
    goalsFor: Optional[int] = None
    goalsAgainst: Optional[int] = None
    place: Optional[int] = None
    playedHome: Optional[int] = None
    wonHome: Optional[int] = None
    drawHome: Optional[int] = None
    lostHome: Optional[int] = None
    goalsForHome: Optional[int] = None
    goalsAgainstHome: Optional[int] = None
    placeHome: Optional[int] = None
    playedAway: Optional[int] = None
    wonAway: Optional[int] = None
    drawAway: Optional[int] = None
    lostAway: Optional[int] = None
    goalsForAway: Optional[int] = None
    goalsAgainstAway: Optional[int] = None
    placeAway: Optional[int] = None
    matchPointsL1Played: Optional[float] = None
    matchPointsL1GoalsAllowed: Optional[float] = None
    matchPointsL1CleanSheet: Optional[float] = None
    matchPointsL1Cards: Optional[float] = None
    matchPointsL1Goals: Optional[float] = None
    matchPointsL1Assists: Optional[float] = None
    matchPointsL1OwnGoals: Optional[float] = None
    matchPointsL1: Optional[float] = None
    pointsL1Played: Optional[float] = None
    pointsL1GoalsAllowed: Optional[float] = None
    pointsL1CleanSheet: Optional[float] = None
    pointsL1Cards: Optional[float] = None
    pointsL1Goals: Optional[float] = None
    pointsL1Assists: Optional[float] = None
    pointsL1OwnGoals: Optional[float] = None
    pointsL1: Optional[float] = None
    livePointsL1: Optional[float] = None
    ranking: Optional[int] = None
    processed: int = Field(sa_type=TINYINT)
    createdIn: datetime
    updatedIn: Optional[datetime] = None


class MatchTeam(SQLModel, table=True):
    __tablename__ = "MatchTeams"

    matchTeamID: Optional[int] = Field(default=None, primary_key=True)
    matchID: int
    matchTeamNum: int = Field(sa_type=TINYINT)
    matchStatus: int = Field(sa_type=TINYINT)
    leagueID: int
    divisionID: int
    season: int
    seasonNum: int
    realCompetitionID: Optional[int] = None
    realCompetitionMatchDay: Optional[int] = None
    realCompetitionMatchDaySort: Optional[int] = None
    competitionType: int = Field(sa_type=TINYINT)
    competitionMatchDay: Optional[int] = None
    competitionLastMatchDay: Optional[int] = None
    competitionMatchNumber: Optional[int] = None
    competitionMatchGroup: Optional[int] = None
    competitionMatchNextGroup: Optional[int] = None
    competitionMatchRound: Optional[int] = None
    competitionMatchLastRound: Optional[int] = None
    matchGroupWinnerTeamID: Optional[int] = None
    userID: Optional[int] = None
    teamID: Optional[int] = None
    teamName: Optional[str] = Field(default=None, max_length=128)
    teamScore: Optional[float] = None
    teamPoints: Optional[int] = None
    teamSeeding: Optional[int] = Field(default=None, sa_type=TINYINT)
    matchDayMapKey: Optional[str] = Field(default=None, max_length=20)
    oppositeUserID: Optional[int] = None
    oppositeTeamID: Optional[int] = None
    oppositeTeamName: Optional[str] = Field(default=None, max_length=128)
    oppositeTeamScore: Optional[float] = None
    oppositeTeamPoints: Optional[int] = None
    oppositeTeamSeeding: Optional[int] = Field(default=None, sa_type=TINYINT)
    oppositeMatchDayMapKey: Optional[str] = Field(default=None, max_length=20)
    lineup: Optional[str] = Field(default=None, max_length=240)
    cntEPLTeam: Optional[int] = Field(default=None, sa_type=TINYINT)
    cntGoalkeeper: Optional[int] = Field(default=None, sa_type=TINYINT)
    cntDefender: Optional[int] = Field(default=None, sa_type=TINYINT)
    cntMidfielder: Optional[int] = Field(default=None, sa_type=TINYINT)
    cntStriker: Optional[int] = Field(default=None, sa_type=TINYINT)
    cntSubstitute: Optional[int] = Field(default=None, sa_type=TINYINT)
    cntInactive: Optional[int] = Field(default=None, sa_type=TINYINT)
    createdBy: Optional[int] = None
    createdIn: datetime
    updatedBy: Optional[int] = None
    updatedIn: Optional[datetime] = None


class Match(SQLModel, table=True):
    __tablename__ = "Matches"

    matchID: Optional[int] = Field(default=None, primary_key=True)
    matchStatus: int = Field(sa_type=TINYINT)
    leagueID: int
    divisionID: int
    season: int
    seasonNum: int
    realCompetitionID: Optional[int] = None
    realCompetitionMatchDay: Optional[int] = None
    realCompetitionMatchDaySort: Optional[int] = None
    competitionType: int = Field(sa_type=TINYINT)
    competitionMatchDay: Optional[int] = None
    competitionLastMatchDay: Optional[int] = None
    competitionMatchNumber: Optional[int] = None
    competitionMatchGroup: Optional[int] = None
    competitionMatchNextGroup: Optional[int] = None
    competitionMatchRound: Optional[int] = None
    competitionMatchLastRound: Optional[int] = None
    matchGroupWinnerTeamID: Optional[int] = None
    firstUserID: Optional[int] = None
    firstTeamID: Optional[int] = None
    firstTeamName: Optional[str] = Field(default=None, max_length=128)
    firstTeamScore: Optional[float] = None
    firstTeamPoints: Optional[int] = None
    firstTeamSeeding: Optional[int] = Field(default=None, sa_type=TINYINT)
    firstMatchDayMapKey: Optional[str] = Field(default=None, max_length=20)
    secondUserID: Optional[int] = None
    secondTeamID: Optional[int] = None
    secondTeamName: Optional[str] = Field(default=None, max_length=128)
    secondTeamScore: Optional[float] = None
    secondTeamPoints: Optional[int] = None
    secondTeamSeeding: Optional[int] = Field(default=None, sa_type=TINYINT)
    secondMatchDayMapKey: Optional[str] = Field(default=None, max_length=20)
    createdBy: Optional[int] = None
    createdIn: datetime
    updatedBy: Optional[int] = None
    updatedIn: Optional[datetime] = None


class RealMatch(SQLModel, table=True):
    __tablename__ = "RealMatches"

    realMatchID: Optional[int] = Field(default=None, primary_key=True)
    realMatchStatus: int = Field(sa_type=TINYINT)
    realMatchType: str = Field(max_length=20)
    realMatchPeriod: Optional[str] = Field(default=None, max_length=20)
    realMatchRealPeriod: Optional[str] = Field(default=None, max_length=20)
    realMatchAttendance: Optional[int] = None
    realMatchDate: datetime
    realMatchDateOffset: Optional[int] = None
    realMatchResultType: Optional[str] = Field(default=None, max_length=20)
    realMatchTime: Optional[int] = None
    realMatchFirstHalfTime: Optional[int] = None
    realMatchSecondHalfTime: Optional[int] = None
    realMatchFirstHalfExtraTime: Optional[int] = None
    realMatchSecondHalfExtraTime: Optional[int] = None
    realMatchEnded: int = Field(sa_type=TINYINT)
    realMatchIgnore: int = Field(sa_type=TINYINT)
    realCompetitionID: int
    realCompetitionUID: str = Field(max_length=20)
    realCompetitionSYMID: str = Field(max_length=20)
    realCompetitionSeasonId: str = Field(max_length=20)
    realCompetitionMatchDay: int
    realCompetitionFirstMatchDay: Optional[int] = None
    realCompetitionLastMatchDay: Optional[int] = None
    baseRealCompetitionID: Optional[int] = None
    extraRealCompetitionID: Optional[int] = None
    realVenueID: Optional[int] = None
    realVenueUID: Optional[str] = Field(default=None, max_length=20)
    firstRealTeamMemberID: Optional[int] = None
    firstRealTeamMemberKey: Optional[str] = Field(default=None, max_length=10)
    firstRealTeamID: Optional[int] = None
    firstRealTeamUID: Optional[str] = Field(default=None, max_length=20)
    firstRealTeamName: Optional[str] = Field(default=None, max_length=128)
    firstRealTeamShortName: Optional[str] = Field(default=None, max_length=10)
    firstRealTeamScore: Optional[int] = None
    firstRealTeamRealScore: Optional[int] = None
    firstRealTeamSide: Optional[str] = Field(default=None, max_length=20)
    firstRealTeamCleanSheet: Optional[int] = Field(default=None, sa_type=TINYINT)
    firstRealTeamResult: Optional[int] = Field(default=None, sa_type=TINYINT)
    firstRealTeamPoints: Optional[int] = Field(default=None, sa_type=TINYINT)
    firstRealTeamNumber: Optional[int] = Field(default=None, sa_type=TINYINT)
    secondRealTeamMemberID: Optional[int] = None
    secondRealTeamMemberKey: Optional[str] = Field(default=None, max_length=10)
    secondRealTeamID: Optional[int] = None
    secondRealTeamUID: Optional[str] = Field(default=None, max_length=20)
    secondRealTeamName: Optional[str] = Field(default=None, max_length=128)
    secondRealTeamShortName: Optional[str] = Field(default=None, max_length=10)
    secondRealTeamScore: Optional[int] = None
    secondRealTeamRealScore: Optional[int] = None
    secondRealTeamSide: Optional[str] = Field(default=None, max_length=20)
    secondRealTeamCleanSheet: Optional[int] = Field(default=None, sa_type=TINYINT)
    secondRealTeamResult: Optional[int] = Field(default=None, sa_type=TINYINT)
    secondRealTeamPoints: Optional[int] = Field(default=None, sa_type=TINYINT)
    secondRealTeamNumber: Optional[int] = Field(default=None, sa_type=TINYINT)
    enabled: int = Field(sa_type=TINYINT)
    lastF7Date: Optional[datetime] = None
    lastF42Date: Optional[datetime] = None
    lastFDate: Optional[datetime] = None
    createdIn: datetime
    updatedIn: Optional[datetime] = None
