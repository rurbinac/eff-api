-- phpMyAdmin SQL Dump
-- version 5.2.2
-- https://www.phpmyadmin.net/
--
-- Host: localhost:3306
-- Generation Time: Jun 02, 2026 at 11:31 AM
-- Server version: 5.7.44-48
-- PHP Version: 8.3.31

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";

--
-- Database: `lt3cil7v_eff_pro`
--

-- --------------------------------------------------------

--
-- Table structure for table `DivisionNotes`
--

CREATE TABLE `DivisionNotes` (
  `divisionNoteID` int(11) NOT NULL,
  `leagueID` int(11) NOT NULL,
  `divisionID` int(11) NOT NULL,
  `teamID` int(11) NOT NULL,
  `userID` int(11) NOT NULL,
  `commissionerID` int(11) NOT NULL,
  `parentDivisionNoteID` int(11) DEFAULT NULL,
  `userName` varchar(128) COLLATE utf8mb4_unicode_520_ci NOT NULL,
  `title` varchar(128) COLLATE utf8mb4_unicode_520_ci NOT NULL,
  `notes` text COLLATE utf8mb4_unicode_520_ci,
  `divisionNoteType` char(1) COLLATE utf8mb4_unicode_520_ci NOT NULL,
  `createdBy` int(11) NOT NULL,
  `createdIn` datetime NOT NULL,
  `updatedBy` int(11) DEFAULT NULL,
  `updatedIn` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;

-- --------------------------------------------------------

--
-- Table structure for table `Divisions`
--

CREATE TABLE `Divisions` (
  `divisionID` int(11) NOT NULL,
  `baseRealCompetitionID` int(11) NOT NULL,
  `extraRealCompetitionID` int(11) DEFAULT NULL,
  `matchDayMapKey` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `leagueID` int(11) NOT NULL,
  `commissionerID` int(11) NOT NULL,
  `prevLeagueID` int(11) DEFAULT NULL,
  `nextLeagueID` int(11) DEFAULT NULL,
  `prevDivisionID` int(11) DEFAULT NULL,
  `nextDivisionID` int(11) DEFAULT NULL,
  `season` smallint(6) NOT NULL,
  `seasonNum` smallint(6) NOT NULL,
  `leagueMatches` tinyint(4) DEFAULT '0',
  `divisionMatches` tinyint(4) DEFAULT '0',
  `draftType` char(1) COLLATE utf8mb4_unicode_520_ci NOT NULL,
  `draftDate` datetime NOT NULL,
  `draftCompleteDate` datetime DEFAULT NULL,
  `draftStatus` smallint(6) NOT NULL,
  `draftTime` smallint(6) NOT NULL,
  `draftingStart` datetime DEFAULT NULL,
  `draftingFinish` datetime DEFAULT NULL,
  `draftingLimit` datetime DEFAULT NULL,
  `draftingRound` smallint(6) DEFAULT NULL,
  `draftingMemberOrder` smallint(6) DEFAULT NULL,
  `draftingTeamOrder` smallint(6) DEFAULT NULL,
  `draftingNextTeamOrder` smallint(6) DEFAULT NULL,
  `draftingUsers` text CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `draftingHooks` smallint(6) NOT NULL DEFAULT '0',
  `franchiseMembers` text COLLATE utf8mb4_unicode_520_ci NOT NULL,
  `firstRealCompetitionMatchDay` smallint(6) DEFAULT NULL,
  `lastRealCompetitionMatchDay` smallint(6) DEFAULT NULL,
  `waiverStatus` smallint(6) NOT NULL,
  `matchDay` smallint(6) DEFAULT NULL,
  `isCupMatchDay` tinyint(1) DEFAULT NULL,
  `isDivisionCupMatchDay` tinyint(1) DEFAULT NULL,
  `totalTeams` smallint(6) NOT NULL,
  `numTeams` smallint(6) NOT NULL,
  `availableTeams` smallint(6) NOT NULL,
  `divisionType` char(1) COLLATE utf8mb4_unicode_520_ci NOT NULL,
  `createdBy` int(11) NOT NULL,
  `createdIn` datetime NOT NULL,
  `updatedBy` int(11) DEFAULT NULL,
  `updatedIn` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;

-- --------------------------------------------------------

--
-- Table structure for table `Leagues`
--

CREATE TABLE `Leagues` (
  `leagueID` int(11) NOT NULL,
  `baseRealCompetitionID` int(11) NOT NULL,
  `extraRealCompetitionID` int(11) DEFAULT NULL,
  `leagueName` varchar(128) COLLATE utf8mb4_unicode_520_ci NOT NULL,
  `leaguePassword` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `commissionerID` int(11) NOT NULL,
  `prevLeagueID` int(11) DEFAULT NULL,
  `nextLeagueID` int(11) DEFAULT NULL,
  `season` smallint(6) NOT NULL,
  `seasonNum` smallint(6) NOT NULL,
  `numDivisions` smallint(6) NOT NULL,
  `leagueType` tinyint(4) NOT NULL,
  `gameType` tinyint(4) NOT NULL,
  `scoringSystem` tinyint(4) NOT NULL,
  `tradeDeadline` datetime NOT NULL,
  `publishLeague` tinyint(1) NOT NULL,
  `seasonStatus` smallint(6) NOT NULL,
  `totalTeams` smallint(6) NOT NULL,
  `availableTeams` smallint(6) NOT NULL,
  `totPromoted` tinyint(4) NOT NULL DEFAULT '2',
  `maxFranchiseMembers` tinyint(4) NOT NULL DEFAULT '2',
  `maxWaiver` smallint(6) NOT NULL,
  `minEPLTeam` smallint(6) NOT NULL,
  `minPlayer` smallint(6) NOT NULL,
  `minGoalkeeper` smallint(6) NOT NULL,
  `minDefender` smallint(6) NOT NULL,
  `minMidfielder` smallint(6) NOT NULL,
  `minStriker` smallint(6) NOT NULL,
  `maxEPLTeam` smallint(6) NOT NULL,
  `maxPlayer` smallint(6) NOT NULL,
  `maxGoalkeeper` smallint(6) NOT NULL,
  `maxDefender` smallint(6) NOT NULL,
  `maxMidfielder` smallint(6) NOT NULL,
  `maxStriker` smallint(6) NOT NULL,
  `autoEPLTeam` smallint(6) NOT NULL,
  `autoGoalkeeper` smallint(6) NOT NULL,
  `autoDefender` smallint(6) NOT NULL,
  `autoMidfielder` smallint(6) NOT NULL,
  `autoStriker` smallint(6) NOT NULL,
  `createdBy` int(11) NOT NULL,
  `createdIn` datetime NOT NULL,
  `updatedBy` int(11) DEFAULT NULL,
  `updatedIn` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;

-- --------------------------------------------------------

--
-- Table structure for table `Lookups`
--

CREATE TABLE `Lookups` (
  `lookupID` int(11) NOT NULL,
  `lookupNum` smallint(6) NOT NULL,
  `position` smallint(6) NOT NULL,
  `lookupKey` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `lookupCode` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `lookupText` varchar(50) COLLATE utf8mb4_unicode_520_ci NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;

-- --------------------------------------------------------

--
-- Table structure for table `MatchDaysMap`
--

CREATE TABLE `MatchDaysMap` (
  `matchDayMapID` int(11) NOT NULL,
  `baseRealCompetitionID` int(11) DEFAULT NULL,
  `extraRealCompetitionID` int(11) DEFAULT NULL,
  `competitionType` tinyint(4) NOT NULL,
  `minNumTeams` smallint(6) NOT NULL,
  `maxNumTeams` smallint(6) NOT NULL,
  `totalMatchDays` smallint(6) NOT NULL,
  `rounds` smallint(6) NOT NULL,
  `firstRealCompetitionMatchDay` smallint(6) NOT NULL,
  `firstRealCompetitionMatchDaySort` smallint(6) DEFAULT NULL,
  `matchDay` smallint(6) NOT NULL,
  `realCompetitionID` int(11) DEFAULT NULL,
  `realCompetitionSYMID` varchar(20) COLLATE utf8mb4_unicode_520_ci NOT NULL,
  `realCompetitionSeasonId` varchar(20) COLLATE utf8mb4_unicode_520_ci NOT NULL,
  `realCompetitionMatchDay` smallint(6) NOT NULL,
  `realCompetitionMatchDaySort` smallint(6) DEFAULT NULL,
  `createdBy` int(11) NOT NULL,
  `createdIn` datetime NOT NULL,
  `updatedBy` int(11) DEFAULT NULL,
  `updatedIn` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;

-- --------------------------------------------------------

--
-- Table structure for table `MatchDaysStatus`
--

CREATE TABLE `MatchDaysStatus` (
  `matchDayStatusID` int(11) NOT NULL,
  `baseRealCompetitionID` int(11) DEFAULT NULL,
  `extraRealCompetitionID` int(11) DEFAULT NULL,
  `matchDayMapKey` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `realCompetitionID` int(11) DEFAULT NULL,
  `realCompetitionSYMID` varchar(20) COLLATE utf8mb4_unicode_520_ci NOT NULL,
  `realCompetitionSeasonId` varchar(20) COLLATE utf8mb4_unicode_520_ci NOT NULL,
  `realCompetitionMatchDay` smallint(6) NOT NULL,
  `realCompetitionMatchDaySort` smallint(6) NOT NULL,
  `prevActiveMatchDayStatusID` int(11) DEFAULT NULL,
  `prevActiveRealCompetitionID` int(11) DEFAULT NULL,
  `prevActiveRealCompetitionSYMID` varchar(20) COLLATE utf8mb4_unicode_520_ci DEFAULT NULL,
  `prevActiveRealCompetitionSeasonId` varchar(20) COLLATE utf8mb4_unicode_520_ci DEFAULT NULL,
  `prevActiveRealCompetitionMatchDay` int(11) DEFAULT NULL,
  `nextActiveMatchDayStatusID` int(11) DEFAULT NULL,
  `nextActiveRealCompetitionID` int(11) DEFAULT NULL,
  `nextActiveRealCompetitionSYMID` varchar(20) COLLATE utf8mb4_unicode_520_ci DEFAULT NULL,
  `nextActiveRealCompetitionSeasonId` varchar(20) COLLATE utf8mb4_unicode_520_ci DEFAULT NULL,
  `nextActiveRealCompetitionMatchDay` int(11) DEFAULT NULL,
  `scriptsStatus` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `active` tinyint(1) NOT NULL,
  `locked` tinyint(1) NOT NULL DEFAULT '0',
  `overlapped` tinyint(1) NOT NULL DEFAULT '0',
  `minAllowedRealMatchDate` datetime DEFAULT NULL,
  `maxAllowedRealMatchDate` datetime DEFAULT NULL,
  `minRealMatchDate` datetime DEFAULT NULL,
  `maxRealMatchDate` datetime DEFAULT NULL,
  `startWaivers` datetime DEFAULT NULL,
  `finishWaivers` datetime DEFAULT NULL,
  `startWaiversSettle` datetime DEFAULT NULL,
  `finishWaiversSettle` datetime DEFAULT NULL,
  `startOpenWaivers` datetime DEFAULT NULL,
  `finishOpenWaivers` datetime DEFAULT NULL,
  `startOpenWaiversSettle` datetime DEFAULT NULL,
  `finishOpenWaiversSettle` datetime DEFAULT NULL,
  `startPreMatch` datetime DEFAULT NULL,
  `finishPreMatch` datetime DEFAULT NULL,
  `startMatch` datetime DEFAULT NULL,
  `finishMatch` datetime DEFAULT NULL,
  `startPostMatch` datetime DEFAULT NULL,
  `finishPostMatch` datetime DEFAULT NULL,
  `startMatchDay` datetime DEFAULT NULL,
  `finishMatchDay` datetime DEFAULT NULL,
  `finishBaseMatchDay` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;

-- --------------------------------------------------------

--
-- Table structure for table `MatchDaysStatusDetail`
--

CREATE TABLE `MatchDaysStatusDetail` (
  `matchDayStatusDetailID` int(11) NOT NULL,
  `matchDayMapKey` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `matchDayStatusID` int(11) NOT NULL,
  `baseRealCompetitionID` int(11) NOT NULL,
  `extraRealCompetitionID` int(11) NOT NULL,
  `realCompetitionID` int(11) NOT NULL,
  `realCompetitionMatchDay` smallint(6) NOT NULL,
  `realCompetitionMatchDaySort` smallint(6) NOT NULL,
  `in_process` tinyint(1) NOT NULL DEFAULT '0',
  `matchDayStatus` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `matchDayStatusNum` tinyint(4) NOT NULL,
  `matchDayStatusStart` datetime NOT NULL,
  `matchDayStatusFinish` datetime NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;

-- --------------------------------------------------------

--
-- Table structure for table `Matches`
--

CREATE TABLE `Matches` (
  `matchID` int(11) NOT NULL,
  `matchStatus` tinyint(4) NOT NULL,
  `leagueID` int(11) NOT NULL,
  `divisionID` int(11) DEFAULT NULL,
  `season` smallint(6) NOT NULL,
  `seasonNum` smallint(6) NOT NULL,
  `realCompetitionID` int(11) NOT NULL,
  `realCompetitionMatchDay` smallint(6) NOT NULL,
  `realCompetitionMatchDaySort` smallint(6) NOT NULL,
  `competitionType` tinyint(4) NOT NULL,
  `competitionMatchDay` smallint(6) DEFAULT NULL,
  `competitionLastMatchDay` smallint(6) DEFAULT NULL,
  `competitionMatchNumber` smallint(6) NOT NULL,
  `competitionMatchGroup` smallint(6) DEFAULT NULL,
  `competitionMatchNextGroup` smallint(6) DEFAULT NULL,
  `competitionMatchRound` smallint(6) DEFAULT NULL,
  `competitionMatchLastRound` smallint(6) DEFAULT NULL,
  `matchGroupWinnerTeamID` int(11) DEFAULT NULL,
  `firstUserID` int(11) DEFAULT NULL,
  `firstTeamID` int(11) DEFAULT NULL,
  `firstTeamName` varchar(128) COLLATE utf8mb4_unicode_520_ci DEFAULT NULL,
  `firstTeamScore` float DEFAULT NULL,
  `firstTeamPoints` smallint(6) DEFAULT NULL,
  `firstTeamSeeding` tinyint(4) DEFAULT NULL,
  `firstMatchDayMapKey` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `secondUserID` int(11) DEFAULT NULL,
  `secondTeamID` int(11) DEFAULT NULL,
  `secondTeamName` varchar(128) COLLATE utf8mb4_unicode_520_ci DEFAULT NULL,
  `secondTeamScore` float DEFAULT NULL,
  `secondTeamPoints` smallint(6) DEFAULT NULL,
  `secondTeamSeeding` tinyint(4) DEFAULT NULL,
  `secondMatchDayMapKey` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `createdBy` int(11) NOT NULL DEFAULT '1',
  `createdIn` datetime NOT NULL,
  `updatedBy` int(11) DEFAULT NULL,
  `updatedIn` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;

-- --------------------------------------------------------

--
-- Table structure for table `MatchTeams`
--

CREATE TABLE `MatchTeams` (
  `matchTeamID` int(11) NOT NULL,
  `matchID` int(11) NOT NULL,
  `matchTeamNum` tinyint(4) NOT NULL,
  `matchStatus` tinyint(4) NOT NULL,
  `leagueID` int(11) NOT NULL,
  `divisionID` int(11) DEFAULT NULL,
  `season` smallint(6) NOT NULL,
  `seasonNum` smallint(6) NOT NULL,
  `realCompetitionID` int(11) NOT NULL,
  `realCompetitionMatchDay` smallint(6) NOT NULL,
  `realCompetitionMatchDaySort` smallint(6) NOT NULL,
  `competitionType` tinyint(4) NOT NULL,
  `competitionMatchDay` smallint(6) DEFAULT NULL,
  `competitionLastMatchDay` smallint(6) DEFAULT NULL,
  `competitionMatchNumber` smallint(6) NOT NULL,
  `competitionMatchGroup` smallint(6) DEFAULT NULL,
  `competitionMatchNextGroup` smallint(6) DEFAULT NULL,
  `competitionMatchRound` smallint(6) DEFAULT NULL,
  `competitionMatchLastRound` smallint(6) DEFAULT NULL,
  `matchGroupWinnerTeamID` int(11) DEFAULT NULL,
  `userID` int(11) DEFAULT NULL,
  `teamID` int(11) DEFAULT NULL,
  `teamName` varchar(128) COLLATE utf8mb4_unicode_520_ci DEFAULT NULL,
  `teamScore` float DEFAULT NULL,
  `teamPoints` smallint(6) DEFAULT NULL,
  `teamSeeding` tinyint(4) DEFAULT NULL,
  `matchDayMapKey` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `oppositeUserID` int(11) DEFAULT NULL,
  `oppositeTeamID` int(11) DEFAULT NULL,
  `oppositeTeamName` varchar(128) COLLATE utf8mb4_unicode_520_ci DEFAULT NULL,
  `oppositeTeamScore` float DEFAULT NULL,
  `oppositeTeamPoints` smallint(6) DEFAULT NULL,
  `oppositeTeamSeeding` tinyint(4) DEFAULT NULL,
  `oppositeMatchDayMapKey` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `lineup` varchar(240) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `cntEPLTeam` tinyint(4) DEFAULT NULL,
  `cntGoalkeeper` tinyint(4) DEFAULT NULL,
  `cntDefender` tinyint(4) DEFAULT NULL,
  `cntMidfielder` tinyint(4) DEFAULT NULL,
  `cntStriker` tinyint(4) DEFAULT NULL,
  `cntSubstitute` tinyint(4) DEFAULT NULL,
  `cntInactive` tinyint(4) DEFAULT NULL,
  `createdBy` int(11) NOT NULL DEFAULT '1',
  `createdIn` datetime NOT NULL,
  `updatedBy` int(11) DEFAULT NULL,
  `updatedIn` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;

-- --------------------------------------------------------

--
-- Table structure for table `ProcessStats`
--

CREATE TABLE `ProcessStats` (
  `processStatID` int(11) NOT NULL,
  `processStatName` varchar(40) COLLATE utf8mb4_unicode_520_ci NOT NULL,
  `stats` json NOT NULL,
  `createdIn` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `expiresIn` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;

-- --------------------------------------------------------

--
-- Table structure for table `RealCompetitions`
--

CREATE TABLE `RealCompetitions` (
  `realCompetitionID` int(11) NOT NULL,
  `prevRealCompetitionID` int(11) DEFAULT NULL,
  `nextRealCompetitionID` int(11) DEFAULT NULL,
  `realCompetitionUID` varchar(20) CHARACTER SET utf8 COLLATE utf8_bin NOT NULL,
  `realCompetitionSYMID` varchar(20) CHARACTER SET utf8 NOT NULL,
  `realCompetitionName` varchar(100) CHARACTER SET utf8 NOT NULL,
  `realCompetitionCountry` varchar(100) CHARACTER SET utf8 NOT NULL,
  `realCompetitionSeasonId` varchar(20) CHARACTER SET utf8 NOT NULL,
  `realCompetitionSeasonName` varchar(100) CHARACTER SET utf8 NOT NULL,
  `realCompetitionFirstMatchDay` smallint(6) NOT NULL,
  `realCompetitionLastMatchDay` smallint(6) NOT NULL,
  `realCompetitionExtraMatchDay` smallint(6) DEFAULT NULL,
  `useExtraRealCompetition` tinyint(1) NOT NULL DEFAULT '1',
  `baseRealCompetitionID` int(11) DEFAULT NULL,
  `extraRealCompetitionID` int(11) DEFAULT NULL,
  `calcStandings` tinyint(1) NOT NULL,
  `lastF7Date` datetime DEFAULT '2000-01-01 00:00:00',
  `lastF42Date` datetime DEFAULT '2000-01-01 00:00:00',
  `lastFDate` datetime DEFAULT '2000-01-01 00:00:00',
  `createdIn` datetime NOT NULL,
  `updatedIn` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;

-- --------------------------------------------------------

--
-- Table structure for table `RealMatches`
--

CREATE TABLE `RealMatches` (
  `realMatchID` int(11) NOT NULL,
  `realMatchStatus` tinyint(4) NOT NULL,
  `realMatchType` varchar(20) CHARACTER SET utf8 NOT NULL,
  `realMatchPeriod` varchar(20) CHARACTER SET utf8 NOT NULL,
  `realMatchRealPeriod` varchar(20) CHARACTER SET utf8 NOT NULL,
  `realMatchAttendance` int(11) DEFAULT NULL,
  `realMatchDate` datetime NOT NULL,
  `realMatchDateOffset` int(11) NOT NULL,
  `realMatchResultType` varchar(20) CHARACTER SET utf8 DEFAULT NULL,
  `realMatchTime` smallint(6) DEFAULT NULL,
  `realMatchFirstHalfTime` smallint(6) DEFAULT NULL,
  `realMatchSecondHalfTime` smallint(6) DEFAULT NULL,
  `realMatchFirstHalfExtraTime` smallint(6) DEFAULT NULL,
  `realMatchSecondHalfExtraTime` smallint(6) DEFAULT NULL,
  `realMatchEnded` tinyint(1) NOT NULL,
  `realMatchIgnore` tinyint(1) NOT NULL DEFAULT '0',
  `realCompetitionID` int(11) NOT NULL,
  `realCompetitionUID` varchar(20) CHARACTER SET utf8 COLLATE utf8_bin NOT NULL,
  `realCompetitionSYMID` varchar(20) CHARACTER SET utf8 NOT NULL,
  `realCompetitionSeasonId` varchar(20) CHARACTER SET utf8 NOT NULL,
  `realCompetitionMatchDay` smallint(6) NOT NULL,
  `realCompetitionFirstMatchDay` smallint(6) NOT NULL,
  `realCompetitionLastMatchDay` smallint(6) NOT NULL,
  `baseRealCompetitionID` int(11) NOT NULL,
  `extraRealCompetitionID` int(11) DEFAULT NULL,
  `realVenueID` int(11) DEFAULT NULL,
  `realVenueUID` varchar(20) CHARACTER SET utf8 COLLATE utf8_bin DEFAULT NULL,
  `firstRealTeamMemberID` int(11) DEFAULT NULL,
  `firstRealTeamMemberKey` varchar(10) CHARACTER SET utf8 COLLATE utf8_bin DEFAULT NULL,
  `firstRealTeamID` int(11) NOT NULL,
  `firstRealTeamUID` varchar(20) CHARACTER SET utf8 COLLATE utf8_bin NOT NULL,
  `firstRealTeamName` varchar(128) CHARACTER SET utf8 NOT NULL,
  `firstRealTeamShortName` varchar(10) CHARACTER SET utf8 DEFAULT NULL,
  `firstRealTeamScore` smallint(6) DEFAULT NULL,
  `firstRealTeamRealScore` smallint(6) DEFAULT NULL,
  `firstRealTeamSide` varchar(20) CHARACTER SET utf8 NOT NULL,
  `firstRealTeamCleanSheet` tinyint(1) DEFAULT NULL,
  `firstRealTeamResult` tinyint(4) DEFAULT NULL,
  `firstRealTeamPoints` tinyint(4) DEFAULT NULL,
  `firstRealTeamNumber` tinyint(4) NOT NULL,
  `secondRealTeamMemberID` int(11) DEFAULT NULL,
  `secondRealTeamMemberKey` varchar(10) CHARACTER SET utf8 COLLATE utf8_bin DEFAULT NULL,
  `secondRealTeamID` int(11) NOT NULL,
  `secondRealTeamUID` varchar(20) CHARACTER SET utf8 COLLATE utf8_bin NOT NULL,
  `secondRealTeamName` varchar(128) CHARACTER SET utf8 NOT NULL,
  `secondRealTeamShortName` varchar(10) CHARACTER SET utf8 DEFAULT NULL,
  `secondRealTeamScore` smallint(6) DEFAULT NULL,
  `secondRealTeamRealScore` smallint(6) DEFAULT NULL,
  `secondRealTeamSide` varchar(20) CHARACTER SET utf8 NOT NULL,
  `secondRealTeamCleanSheet` tinyint(1) DEFAULT NULL,
  `secondRealTeamResult` tinyint(4) DEFAULT NULL,
  `secondRealTeamPoints` tinyint(4) DEFAULT NULL,
  `secondRealTeamNumber` tinyint(4) NOT NULL,
  `enabled` tinyint(1) NOT NULL DEFAULT '1',
  `lastF7Date` datetime NOT NULL DEFAULT '2000-01-01 00:00:00',
  `lastF42Date` datetime NOT NULL DEFAULT '2000-01-01 00:00:00',
  `lastFDate` datetime NOT NULL DEFAULT '2000-01-01 00:00:00',
  `createdIn` datetime NOT NULL,
  `updatedIn` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;

-- --------------------------------------------------------

--
-- Table structure for table `RealMatchEvents`
--

CREATE TABLE `RealMatchEvents` (
  `realMatchEventID` int(11) NOT NULL,
  `realMatchID` int(11) NOT NULL,
  `realMatchTeamID` int(11) NOT NULL,
  `realTeamID` int(11) NOT NULL,
  `realPlayerID` int(11) NOT NULL,
  `eventPeriod` tinyint(4) DEFAULT NULL,
  `eventTime` tinyint(4) DEFAULT NULL,
  `eventMin` tinyint(4) DEFAULT NULL,
  `eventSec` tinyint(4) DEFAULT NULL,
  `eventNumber` int(11) DEFAULT NULL,
  `eventTimeStamp` datetime DEFAULT NULL,
  `eventReason` varchar(20) COLLATE utf8mb4_unicode_520_ci NOT NULL,
  `eventType` varchar(20) COLLATE utf8mb4_unicode_520_ci DEFAULT NULL,
  `eventClass` varchar(12) COLLATE utf8mb4_unicode_520_ci DEFAULT NULL,
  `createdIn` datetime NOT NULL,
  `updatedIn` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;

-- --------------------------------------------------------

--
-- Table structure for table `RealMatchPlayers`
--

CREATE TABLE `RealMatchPlayers` (
  `realMatchPlayerID` int(11) NOT NULL,
  `realMatchID` int(11) NOT NULL,
  `realStandingID` int(11) DEFAULT NULL,
  `realMatchStatus` tinyint(4) NOT NULL,
  `realMatchPeriod` varchar(20) CHARACTER SET utf8 NOT NULL,
  `realMatchRealPeriod` varchar(20) CHARACTER SET utf8 NOT NULL,
  `realMatchDate` datetime NOT NULL,
  `realMatchDateOffset` int(11) NOT NULL,
  `realMatchTime` smallint(6) DEFAULT NULL,
  `realMatchEnded` tinyint(1) NOT NULL,
  `realCompetitionID` int(11) NOT NULL,
  `realCompetitionUID` varchar(20) CHARACTER SET utf8 COLLATE utf8_bin NOT NULL,
  `realCompetitionSYMID` varchar(20) CHARACTER SET utf8 NOT NULL,
  `realCompetitionSeasonId` varchar(20) CHARACTER SET utf8 NOT NULL,
  `realCompetitionMatchDay` smallint(6) NOT NULL,
  `realCompetitionFirstMatchDay` smallint(6) NOT NULL,
  `realCompetitionLastMatchDay` smallint(6) NOT NULL,
  `baseRealCompetitionID` int(11) NOT NULL,
  `extraRealCompetitionID` int(11) DEFAULT NULL,
  `realVenueID` int(11) DEFAULT NULL,
  `realVenueUID` varchar(20) CHARACTER SET utf8 COLLATE utf8_bin DEFAULT NULL,
  `realMatchTeamID` int(11) NOT NULL,
  `realTeamID` int(11) NOT NULL,
  `realTeamUID` varchar(20) CHARACTER SET utf8 COLLATE utf8_bin NOT NULL,
  `realTeamName` varchar(128) CHARACTER SET utf8 NOT NULL,
  `realTeamShortName` varchar(10) CHARACTER SET utf8 DEFAULT NULL,
  `realTeamScore` smallint(6) DEFAULT NULL,
  `realTeamRealScore` smallint(6) DEFAULT NULL,
  `realTeamSide` varchar(20) CHARACTER SET utf8 NOT NULL,
  `realTeamCleanSheet` tinyint(1) DEFAULT NULL,
  `realTeamResult` tinyint(4) DEFAULT NULL,
  `realTeamPoints` tinyint(4) DEFAULT NULL,
  `realTeamNumber` tinyint(4) NOT NULL,
  `oppositeRealTeamID` int(11) NOT NULL,
  `oppositeRealTeamUID` varchar(20) CHARACTER SET utf8 COLLATE utf8_bin NOT NULL,
  `oppositeRealTeamName` varchar(128) CHARACTER SET utf8 NOT NULL,
  `oppositeRealTeamShortName` varchar(10) CHARACTER SET utf8 DEFAULT NULL,
  `oppositeRealTeamScore` smallint(6) DEFAULT NULL,
  `oppositeRealTeamRealScore` smallint(6) DEFAULT NULL,
  `oppositeRealTeamSide` varchar(20) CHARACTER SET utf8 NOT NULL,
  `oppositeRealTeamCleanSheet` tinyint(1) DEFAULT NULL,
  `oppositeRealTeamResult` tinyint(4) DEFAULT NULL,
  `oppositeRealTeamPoints` tinyint(4) DEFAULT NULL,
  `oppositeRealTeamNumber` tinyint(4) NOT NULL,
  `realTeamMemberID` int(11) DEFAULT NULL,
  `realTeamMemberKey` varchar(10) CHARACTER SET utf8 COLLATE utf8_bin DEFAULT NULL,
  `realPlayerID` int(11) NOT NULL,
  `realPlayerUID` varchar(20) CHARACTER SET utf8 COLLATE utf8_bin NOT NULL,
  `firstName` varchar(100) CHARACTER SET utf8 NOT NULL,
  `lastName` varchar(100) CHARACTER SET utf8 NOT NULL,
  `knownName` varchar(100) CHARACTER SET utf8 DEFAULT NULL,
  `position` varchar(20) CHARACTER SET utf8 NOT NULL,
  `draftPosition` varchar(20) CHARACTER SET utf8 DEFAULT NULL,
  `draftPositionOrder` tinyint(4) DEFAULT NULL,
  `startStatus` varchar(20) CHARACTER SET utf8 NOT NULL,
  `shirtNumber` smallint(6) DEFAULT NULL,
  `timeIn` smallint(6) DEFAULT NULL,
  `timeOut` smallint(6) DEFAULT NULL,
  `timePlayed` smallint(6) DEFAULT NULL,
  `startedGame` tinyint(1) DEFAULT NULL,
  `finishedGame` tinyint(1) DEFAULT NULL,
  `fullGame` tinyint(1) DEFAULT NULL,
  `gamePlayed` tinyint(1) DEFAULT NULL,
  `yellowCards` int(11) DEFAULT NULL,
  `secondYellowCards` int(11) DEFAULT NULL,
  `straightRedCards` int(11) DEFAULT NULL,
  `redCards` int(11) DEFAULT NULL,
  `goals` int(11) DEFAULT NULL,
  `assists` int(11) DEFAULT NULL,
  `ownGoals` int(11) DEFAULT NULL,
  `goalsConceded` int(11) DEFAULT NULL,
  `penaltiesWon` int(11) DEFAULT NULL,
  `penaltiesConceded` int(11) DEFAULT NULL,
  `accuratePasses` int(11) DEFAULT NULL,
  `unsuccessfulPasses` int(11) DEFAULT NULL,
  `tackle` int(11) DEFAULT NULL,
  `dispossessed` int(11) DEFAULT NULL,
  `interception` int(11) DEFAULT NULL,
  `fouls` int(11) DEFAULT NULL,
  `saves` int(11) DEFAULT NULL,
  `penaltySaves` int(11) DEFAULT NULL,
  `goalKicks` int(11) DEFAULT NULL,
  `cleanSheet` int(11) DEFAULT NULL,
  `pointsL1GoalkeeperPlayed` float DEFAULT NULL,
  `pointsL1GoalkeeperGoalsAllowed` float DEFAULT NULL,
  `pointsL1GoalkeeperCleanSheet` float DEFAULT NULL,
  `pointsL1GoalkeeperCards` float DEFAULT NULL,
  `pointsL1GoalkeeperGoals` float DEFAULT NULL,
  `pointsL1GoalkeeperAssists` float DEFAULT NULL,
  `pointsL1GoalkeeperOwnGoals` float DEFAULT NULL,
  `pointsL1Goalkeeper` float DEFAULT NULL,
  `pointsL1DefenderPlayed` float DEFAULT NULL,
  `pointsL1DefenderGoalsAllowed` float DEFAULT NULL,
  `pointsL1DefenderCleanSheet` float DEFAULT NULL,
  `pointsL1DefenderCards` float DEFAULT NULL,
  `pointsL1DefenderGoals` float DEFAULT NULL,
  `pointsL1DefenderAssists` float DEFAULT NULL,
  `pointsL1DefenderOwnGoals` float DEFAULT NULL,
  `pointsL1Defender` float DEFAULT NULL,
  `pointsL1MidfielderPlayed` float DEFAULT NULL,
  `pointsL1MidfielderGoalsAllowed` float DEFAULT NULL,
  `pointsL1MidfielderCleanSheet` float DEFAULT NULL,
  `pointsL1MidfielderCards` float DEFAULT NULL,
  `pointsL1MidfielderGoals` float DEFAULT NULL,
  `pointsL1MidfielderAssists` float DEFAULT NULL,
  `pointsL1MidfielderOwnGoals` float DEFAULT NULL,
  `pointsL1Midfielder` float DEFAULT NULL,
  `pointsL1StrikerPlayed` float DEFAULT NULL,
  `pointsL1StrikerGoalsAllowed` float DEFAULT NULL,
  `pointsL1StrikerCleanSheet` float DEFAULT NULL,
  `pointsL1StrikerCards` float DEFAULT NULL,
  `pointsL1StrikerGoals` float DEFAULT NULL,
  `pointsL1StrikerAssists` float DEFAULT NULL,
  `pointsL1StrikerOwnGoals` float DEFAULT NULL,
  `pointsL1Striker` float DEFAULT NULL,
  `lastF7Date` datetime NOT NULL DEFAULT '2000-01-01 00:00:00',
  `lastF42Date` datetime NOT NULL DEFAULT '2000-01-01 00:00:00',
  `lastFDate` datetime NOT NULL DEFAULT '2000-01-01 00:00:00',
  `createdIn` datetime NOT NULL,
  `updatedIn` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;

-- --------------------------------------------------------

--
-- Table structure for table `RealMatchTeams`
--

CREATE TABLE `RealMatchTeams` (
  `realMatchTeamID` int(11) NOT NULL,
  `realMatchID` int(11) NOT NULL,
  `realMatchStatus` tinyint(4) NOT NULL,
  `realMatchType` varchar(20) CHARACTER SET utf8 NOT NULL,
  `realMatchPeriod` varchar(20) CHARACTER SET utf8 NOT NULL,
  `realMatchRealPeriod` varchar(20) CHARACTER SET utf8 NOT NULL,
  `realMatchAttendance` int(11) DEFAULT NULL,
  `realMatchDate` datetime NOT NULL,
  `realMatchDateOffset` int(11) NOT NULL,
  `realMatchResultType` varchar(20) CHARACTER SET utf8 DEFAULT NULL,
  `realMatchTime` smallint(6) DEFAULT NULL,
  `realMatchFirstHalfTime` smallint(6) DEFAULT NULL,
  `realMatchSecondHalfTime` smallint(6) DEFAULT NULL,
  `realMatchFirstHalfExtraTime` smallint(6) DEFAULT NULL,
  `realMatchSecondHalfExtraTime` smallint(6) DEFAULT NULL,
  `realMatchEnded` tinyint(1) NOT NULL,
  `realMatchIgnore` tinyint(1) NOT NULL DEFAULT '0',
  `realCompetitionID` int(11) NOT NULL,
  `realCompetitionUID` varchar(20) CHARACTER SET utf8 COLLATE utf8_bin NOT NULL,
  `realCompetitionSYMID` varchar(20) CHARACTER SET utf8 NOT NULL,
  `realCompetitionSeasonId` varchar(20) CHARACTER SET utf8 NOT NULL,
  `realCompetitionMatchDay` smallint(6) NOT NULL,
  `realCompetitionFirstMatchDay` smallint(6) NOT NULL,
  `realCompetitionLastMatchDay` smallint(6) NOT NULL,
  `baseRealCompetitionID` int(11) NOT NULL,
  `extraRealCompetitionID` int(11) DEFAULT NULL,
  `realVenueID` int(11) DEFAULT NULL,
  `realVenueUID` varchar(20) CHARACTER SET utf8 COLLATE utf8_bin DEFAULT NULL,
  `realTeamMemberID` int(11) DEFAULT NULL,
  `realTeamMemberKey` varchar(10) CHARACTER SET utf8 COLLATE utf8_bin DEFAULT NULL,
  `realTeamID` int(11) NOT NULL,
  `realTeamUID` varchar(20) CHARACTER SET utf8 COLLATE utf8_bin NOT NULL,
  `realTeamName` varchar(128) CHARACTER SET utf8 NOT NULL,
  `realTeamShortName` varchar(10) CHARACTER SET utf8 DEFAULT NULL,
  `realTeamScore` smallint(6) DEFAULT NULL,
  `realTeamRealScore` smallint(6) DEFAULT NULL,
  `realTeamSide` varchar(20) CHARACTER SET utf8 NOT NULL,
  `realTeamCleanSheet` tinyint(1) DEFAULT NULL,
  `realTeamResult` tinyint(4) DEFAULT NULL,
  `realTeamPoints` tinyint(4) DEFAULT NULL,
  `realTeamNumber` tinyint(4) NOT NULL,
  `oppositeRealTeamMemberID` int(11) DEFAULT NULL,
  `oppositeRealTeamMemberKey` varchar(10) CHARACTER SET utf8 COLLATE utf8_bin DEFAULT NULL,
  `oppositeRealTeamID` int(11) NOT NULL,
  `oppositeRealTeamUID` varchar(20) CHARACTER SET utf8 COLLATE utf8_bin NOT NULL,
  `oppositeRealTeamName` varchar(128) CHARACTER SET utf8 NOT NULL,
  `oppositeRealTeamShortName` varchar(10) CHARACTER SET utf8 DEFAULT NULL,
  `oppositeRealTeamScore` smallint(6) DEFAULT NULL,
  `oppositeRealTeamRealScore` smallint(6) DEFAULT NULL,
  `oppositeRealTeamSide` varchar(20) CHARACTER SET utf8 NOT NULL,
  `oppositeRealTeamCleanSheet` tinyint(1) DEFAULT NULL,
  `oppositeRealTeamResult` tinyint(4) DEFAULT NULL,
  `oppositeRealTeamPoints` tinyint(4) DEFAULT NULL,
  `oppositeRealTeamNumber` tinyint(4) NOT NULL,
  `enabled` tinyint(1) NOT NULL DEFAULT '1',
  `pointsL1` float DEFAULT NULL,
  `lastF7Date` datetime NOT NULL DEFAULT '2000-01-01 00:00:00',
  `lastF42Date` datetime NOT NULL DEFAULT '2000-01-01 00:00:00',
  `lastFDate` datetime NOT NULL DEFAULT '2000-01-01 00:00:00',
  `createdIn` datetime NOT NULL,
  `updatedIn` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;

-- --------------------------------------------------------

--
-- Table structure for table `RealPlayers`
--

CREATE TABLE `RealPlayers` (
  `realPlayerID` int(11) NOT NULL,
  `prevRealPlayerID` int(11) DEFAULT NULL,
  `nextRealPlayerID` int(11) DEFAULT NULL,
  `realCompetitionID` int(11) NOT NULL,
  `realCompetitionUID` varchar(20) CHARACTER SET utf8 COLLATE utf8_bin NOT NULL,
  `realCompetitionSYMID` varchar(20) CHARACTER SET utf8 NOT NULL,
  `realCompetitionSeasonId` varchar(20) CHARACTER SET utf8 NOT NULL,
  `baseRealCompetitionID` int(11) NOT NULL,
  `extraRealCompetitionID` int(11) DEFAULT NULL,
  `isProcessedMember` tinyint(1) NOT NULL DEFAULT '0',
  `realTeamMemberID` int(11) DEFAULT NULL,
  `realTeamMemberKey` varchar(10) CHARACTER SET utf8 COLLATE utf8_bin DEFAULT NULL,
  `realTeamID` int(11) NOT NULL,
  `realTeamUID` varchar(20) CHARACTER SET utf8 COLLATE utf8_bin NOT NULL,
  `baseRealTeamID` int(11) DEFAULT NULL,
  `baseRealTeamUID` varchar(20) CHARACTER SET utf8 COLLATE utf8_bin DEFAULT NULL,
  `baseRealTeamName` varchar(128) CHARACTER SET utf8 DEFAULT NULL,
  `baseRealTeamShortName` varchar(10) CHARACTER SET utf8 DEFAULT NULL,
  `realPlayerUID` varchar(20) CHARACTER SET utf8 COLLATE utf8_bin NOT NULL,
  `baseRealPlayerID` int(11) DEFAULT NULL,
  `firstName` varchar(100) CHARACTER SET utf8 NOT NULL,
  `lastName` varchar(100) CHARACTER SET utf8 NOT NULL,
  `knownName` varchar(100) CHARACTER SET utf8 DEFAULT NULL,
  `position` varchar(20) CHARACTER SET utf8 DEFAULT NULL,
  `realPosition` varchar(20) CHARACTER SET utf8 DEFAULT NULL,
  `draftPosition` varchar(20) CHARACTER SET utf8 DEFAULT NULL,
  `draftPositionOrder` tinyint(4) DEFAULT NULL,
  `birthDate` date DEFAULT NULL,
  `weight` float DEFAULT NULL,
  `height` float DEFAULT NULL,
  `jerseyNumber` smallint(6) DEFAULT NULL,
  `ranking` int(11) DEFAULT NULL,
  `lastF7Date` datetime NOT NULL DEFAULT '2000-01-01 00:00:00',
  `lastF42Date` datetime NOT NULL DEFAULT '2000-01-01 00:00:00',
  `lastFDate` datetime NOT NULL DEFAULT '2000-01-01 00:00:00',
  `createdIn` datetime NOT NULL,
  `updatedIn` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;

-- --------------------------------------------------------

--
-- Table structure for table `RealStandings`
--

CREATE TABLE `RealStandings` (
  `realStandingID` int(11) NOT NULL,
  `realTeamMemberID` int(11) NOT NULL,
  `realTeamMemberKey` varchar(10) CHARACTER SET utf8 COLLATE utf8_bin NOT NULL,
  `prevRealTeamMemberKey` varchar(10) CHARACTER SET utf8 COLLATE utf8_bin DEFAULT NULL,
  `nextRealTeamMemberKey` varchar(10) CHARACTER SET utf8 COLLATE utf8_bin DEFAULT NULL,
  `realCompetitionID` int(11) NOT NULL,
  `realCompetitionUID` varchar(20) CHARACTER SET utf8 COLLATE utf8_bin NOT NULL,
  `realCompetitionSYMID` varchar(20) CHARACTER SET utf8 NOT NULL,
  `realCompetitionSeasonId` varchar(20) CHARACTER SET utf8 NOT NULL,
  `realCompetitionMatchDay` smallint(6) NOT NULL,
  `realCompetitionLastMatchDay` smallint(6) NOT NULL,
  `baseRealCompetitionID` int(11) NOT NULL,
  `extraRealCompetitionID` int(11) DEFAULT NULL,
  `isTeam` tinyint(1) NOT NULL,
  `isPlayer` tinyint(1) NOT NULL,
  `baseMatchDay` smallint(6) NOT NULL,
  `realMatchID` int(11) DEFAULT NULL,
  `realMatchTeamID` int(11) DEFAULT NULL,
  `realMatchDate` datetime DEFAULT NULL,
  `realMatchTime` smallint(6) DEFAULT NULL,
  `realMatchStatus` tinyint(4) DEFAULT NULL,
  `realTeamID` int(11) DEFAULT NULL,
  `realTeamUID` varchar(20) CHARACTER SET utf8 COLLATE utf8_bin DEFAULT NULL,
  `realTeamName` varchar(128) CHARACTER SET utf8 DEFAULT NULL,
  `realTeamShortName` varchar(10) CHARACTER SET utf8 DEFAULT NULL,
  `realTeamScore` smallint(6) DEFAULT NULL,
  `realTeamSide` varchar(20) CHARACTER SET utf8 DEFAULT NULL,
  `oppositeRealTeamID` int(11) DEFAULT NULL,
  `oppositeRealTeamUID` varchar(20) CHARACTER SET utf8 COLLATE utf8_bin DEFAULT NULL,
  `oppositeRealTeamName` varchar(128) CHARACTER SET utf8 DEFAULT NULL,
  `oppositeRealTeamShortName` varchar(10) CHARACTER SET utf8 DEFAULT NULL,
  `oppositeRealTeamScore` smallint(6) DEFAULT NULL,
  `realPlayerID` int(11) DEFAULT NULL,
  `realPlayerUID` varchar(20) CHARACTER SET utf8 COLLATE utf8_bin DEFAULT NULL,
  `firstName` varchar(100) CHARACTER SET utf8 DEFAULT NULL,
  `lastName` varchar(100) CHARACTER SET utf8 DEFAULT NULL,
  `knownName` varchar(100) CHARACTER SET utf8 DEFAULT NULL,
  `name` varchar(100) CHARACTER SET utf8 DEFAULT NULL,
  `sortName` varchar(100) CHARACTER SET utf8 DEFAULT NULL,
  `position` varchar(20) CHARACTER SET utf8 NOT NULL,
  `draftPosition` varchar(20) CHARACTER SET utf8 NOT NULL,
  `draftPositionOrder` tinyint(4) DEFAULT NULL,
  `timePlayed` int(11) DEFAULT NULL,
  `gamePlayed` int(11) DEFAULT NULL,
  `goals` int(11) DEFAULT NULL,
  `assists` int(11) DEFAULT NULL,
  `yellowCards` int(11) DEFAULT NULL,
  `redCards` int(11) DEFAULT NULL,
  `goalsConceded` int(11) DEFAULT NULL,
  `cleanSheet` int(11) DEFAULT NULL,
  `matchTimePlayed` int(11) DEFAULT NULL,
  `matchGamePlayed` int(11) DEFAULT NULL,
  `matchGoals` int(11) DEFAULT NULL,
  `matchAssists` int(11) DEFAULT NULL,
  `matchYellowCards` int(11) DEFAULT NULL,
  `matchRedCards` int(11) DEFAULT NULL,
  `matchGoalsConceded` int(11) DEFAULT NULL,
  `matchCleanSheet` int(11) DEFAULT NULL,
  `matchDayPlayed` int(11) DEFAULT NULL,
  `matchWon` int(11) DEFAULT NULL,
  `matchDraw` int(11) DEFAULT NULL,
  `matchLost` int(11) DEFAULT NULL,
  `played` smallint(6) DEFAULT NULL,
  `won` smallint(6) DEFAULT NULL,
  `draw` smallint(6) DEFAULT NULL,
  `lost` smallint(6) DEFAULT NULL,
  `goalsFor` smallint(6) DEFAULT NULL,
  `goalsAgainst` smallint(6) DEFAULT NULL,
  `place` smallint(6) DEFAULT NULL,
  `playedHome` smallint(6) DEFAULT NULL,
  `wonHome` smallint(6) DEFAULT NULL,
  `drawHome` smallint(6) DEFAULT NULL,
  `lostHome` smallint(6) DEFAULT NULL,
  `goalsForHome` smallint(6) DEFAULT NULL,
  `goalsAgainstHome` smallint(6) DEFAULT NULL,
  `placeHome` smallint(6) DEFAULT NULL,
  `playedAway` smallint(6) DEFAULT NULL,
  `wonAway` smallint(6) DEFAULT NULL,
  `drawAway` smallint(6) DEFAULT NULL,
  `lostAway` smallint(6) DEFAULT NULL,
  `goalsForAway` smallint(6) DEFAULT NULL,
  `goalsAgainstAway` smallint(6) DEFAULT NULL,
  `placeAway` smallint(6) DEFAULT NULL,
  `matchPointsL1Played` float DEFAULT NULL,
  `matchPointsL1GoalsAllowed` float DEFAULT NULL,
  `matchPointsL1CleanSheet` float DEFAULT NULL,
  `matchPointsL1Cards` float DEFAULT NULL,
  `matchPointsL1Goals` float DEFAULT NULL,
  `matchPointsL1Assists` float DEFAULT NULL,
  `matchPointsL1OwnGoals` float DEFAULT NULL,
  `matchPointsL1` float DEFAULT NULL,
  `pointsL1Played` float DEFAULT NULL,
  `pointsL1GoalsAllowed` float DEFAULT NULL,
  `pointsL1CleanSheet` float DEFAULT NULL,
  `pointsL1Cards` float DEFAULT NULL,
  `pointsL1Goals` float DEFAULT NULL,
  `pointsL1Assists` float DEFAULT NULL,
  `pointsL1OwnGoals` float DEFAULT NULL,
  `pointsL1` float DEFAULT NULL,
  `livePointsL1` float DEFAULT NULL,
  `ranking` smallint(6) DEFAULT NULL,
  `processed` tinyint(1) NOT NULL,
  `createdIn` datetime NOT NULL,
  `updatedIn` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;

-- --------------------------------------------------------

--
-- Table structure for table `RealTeamMembers`
--

CREATE TABLE `RealTeamMembers` (
  `realTeamMemberID` int(11) NOT NULL,
  `realTeamMemberKey` varchar(10) CHARACTER SET utf8 COLLATE utf8_bin NOT NULL,
  `prevRealTeamMemberKey` varchar(10) CHARACTER SET utf8 COLLATE utf8_bin DEFAULT NULL,
  `nextRealTeamMemberKey` varchar(10) CHARACTER SET utf8 COLLATE utf8_bin DEFAULT NULL,
  `baseRealCompetitionID` int(11) NOT NULL,
  `extraRealCompetitionID` int(11) DEFAULT NULL,
  `isTeam` tinyint(1) NOT NULL,
  `isPlayer` tinyint(1) NOT NULL,
  `realTeamID` int(11) DEFAULT NULL,
  `realTeamUID` varchar(20) CHARACTER SET utf8 COLLATE utf8_bin NOT NULL,
  `realTeamName` varchar(128) CHARACTER SET utf8 NOT NULL,
  `realTeamShortName` varchar(10) CHARACTER SET utf8 DEFAULT NULL,
  `realPlayerID` int(11) DEFAULT NULL,
  `realPlayerUID` varchar(20) CHARACTER SET utf8 COLLATE utf8_bin DEFAULT NULL,
  `firstName` varchar(100) CHARACTER SET utf8 DEFAULT NULL,
  `lastName` varchar(100) CHARACTER SET utf8 DEFAULT NULL,
  `knownName` varchar(100) CHARACTER SET utf8 DEFAULT NULL,
  `name` varchar(100) CHARACTER SET utf8 NOT NULL,
  `sortName` varchar(100) CHARACTER SET utf8 NOT NULL,
  `position` varchar(20) CHARACTER SET utf8 DEFAULT NULL,
  `draftPosition` varchar(20) CHARACTER SET utf8 DEFAULT NULL,
  `draftPositionOrder` tinyint(4) DEFAULT NULL,
  `birthDate` date DEFAULT NULL,
  `weight` float DEFAULT NULL,
  `height` float DEFAULT NULL,
  `jerseyNumber` smallint(6) DEFAULT NULL,
  `enabled` tinyint(1) NOT NULL,
  `last_ranking` int(11) DEFAULT NULL,
  `last_timePlayed` int(11) DEFAULT NULL,
  `last_gamePlayed` int(11) DEFAULT NULL,
  `last_goals` int(11) DEFAULT NULL,
  `last_assists` int(11) DEFAULT NULL,
  `last_goalsConceded` int(11) DEFAULT NULL,
  `last_yellowCards` int(11) DEFAULT NULL,
  `last_redCards` int(11) DEFAULT NULL,
  `last_cleanSheet` int(11) DEFAULT NULL,
  `last_played` smallint(6) DEFAULT NULL,
  `last_won` smallint(6) DEFAULT NULL,
  `last_draw` smallint(6) DEFAULT NULL,
  `last_lost` smallint(6) DEFAULT NULL,
  `last_goalsFor` smallint(6) DEFAULT NULL,
  `last_goalsAgainst` smallint(6) DEFAULT NULL,
  `last_pointsL1` float DEFAULT NULL,
  `ranking` int(11) DEFAULT NULL,
  `timePlayed` int(11) DEFAULT NULL,
  `gamePlayed` int(11) DEFAULT NULL,
  `goals` int(11) DEFAULT NULL,
  `assists` int(11) DEFAULT NULL,
  `goalsConceded` int(11) DEFAULT NULL,
  `yellowCards` int(11) DEFAULT NULL,
  `redCards` int(11) DEFAULT NULL,
  `cleanSheet` int(11) DEFAULT NULL,
  `played` smallint(6) DEFAULT NULL,
  `won` smallint(6) DEFAULT NULL,
  `draw` smallint(6) DEFAULT NULL,
  `lost` smallint(6) DEFAULT NULL,
  `goalsFor` smallint(6) DEFAULT NULL,
  `goalsAgainst` smallint(6) DEFAULT NULL,
  `pointsL1` float DEFAULT NULL,
  `livePointsL1` float DEFAULT NULL,
  `lastF7Date` datetime NOT NULL DEFAULT '2000-01-01 00:00:00',
  `lastF42Date` datetime NOT NULL DEFAULT '2000-01-01 00:00:00',
  `lastFDate` datetime NOT NULL DEFAULT '2000-01-01 00:00:00',
  `createdIn` datetime NOT NULL,
  `updatedIn` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;

-- --------------------------------------------------------

--
-- Table structure for table `RealTeams`
--

CREATE TABLE `RealTeams` (
  `realTeamID` int(11) NOT NULL,
  `prevRealTeamID` int(11) DEFAULT NULL,
  `nextRealTeamID` int(11) DEFAULT NULL,
  `realTeamUID` varchar(20) CHARACTER SET utf8 COLLATE utf8_bin NOT NULL,
  `realTeamSYMID` varchar(20) CHARACTER SET utf8 DEFAULT NULL,
  `realTeamCountry` varchar(128) CHARACTER SET utf8 NOT NULL,
  `realTeamName` varchar(128) CHARACTER SET utf8 NOT NULL,
  `realTeamShortName` varchar(10) CHARACTER SET utf8 DEFAULT NULL,
  `baseRealTeamID` int(11) DEFAULT NULL,
  `baseRealTeamUID` varchar(20) CHARACTER SET utf8 COLLATE utf8_bin DEFAULT NULL,
  `baseRealTeamName` varchar(128) CHARACTER SET utf8 DEFAULT NULL,
  `baseRealTeamShortName` varchar(10) CHARACTER SET utf8 DEFAULT NULL,
  `realCompetitionID` int(11) NOT NULL,
  `realCompetitionUID` varchar(20) CHARACTER SET utf8 COLLATE utf8_bin NOT NULL,
  `realCompetitionSYMID` varchar(20) CHARACTER SET utf8 NOT NULL,
  `realCompetitionSeasonId` varchar(20) CHARACTER SET utf8 NOT NULL,
  `baseRealCompetitionID` int(11) NOT NULL,
  `extraRealCompetitionID` int(11) DEFAULT NULL,
  `isProcessedMember` tinyint(1) NOT NULL DEFAULT '0',
  `realTeamMemberID` int(11) DEFAULT NULL,
  `realTeamMemberKey` varchar(10) CHARACTER SET utf8 COLLATE utf8_bin DEFAULT NULL,
  `shortName` varchar(20) CHARACTER SET utf8 DEFAULT NULL,
  `sortNumber` smallint(6) DEFAULT NULL,
  `jerseyStyle` smallint(6) DEFAULT NULL,
  `shortStyle` smallint(6) DEFAULT NULL,
  `realTeamAvatar` varchar(128) CHARACTER SET utf8 COLLATE utf8_bin DEFAULT NULL,
  `ranking` int(11) DEFAULT NULL,
  `position` varchar(20) CHARACTER SET utf8 DEFAULT NULL,
  `draftPosition` varchar(20) CHARACTER SET utf8 DEFAULT NULL,
  `draftPositionOrder` tinyint(4) DEFAULT NULL,
  `lastF7Date` datetime NOT NULL DEFAULT '2000-01-01 00:00:00',
  `lastF42Date` datetime NOT NULL DEFAULT '2000-01-01 00:00:00',
  `lastFDate` datetime NOT NULL DEFAULT '2000-01-01 00:00:00',
  `createdIn` datetime NOT NULL,
  `updatedIn` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;

-- --------------------------------------------------------

--
-- Table structure for table `RealVenues`
--

CREATE TABLE `RealVenues` (
  `realVenueID` int(11) NOT NULL,
  `realVenueUID` varchar(20) CHARACTER SET utf8 COLLATE utf8_bin DEFAULT NULL,
  `realVenueCountry` varchar(100) COLLATE utf8mb4_unicode_520_ci DEFAULT NULL,
  `realVenueName` varchar(100) COLLATE utf8mb4_unicode_520_ci DEFAULT NULL,
  `lastF7Date` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `lastF42Date` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `lastFDate` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `createdIn` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updatedIn` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;

-- --------------------------------------------------------

--
-- Table structure for table `Tasks`
--

CREATE TABLE `Tasks` (
  `taskID` int(11) NOT NULL,
  `parentTaskID` int(11) DEFAULT NULL,
  `taskName` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `startTS` datetime NOT NULL,
  `finishTS` datetime NOT NULL,
  `elapsed` double NOT NULL,
  `count` int(11) DEFAULT NULL,
  `state` enum('running','success','failure') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'running',
  `messages` json DEFAULT NULL,
  `issues` json DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;

-- --------------------------------------------------------

--
-- Table structure for table `TeamMemberLog`
--

CREATE TABLE `TeamMemberLog` (
  `teamMemberLogID` int(11) NOT NULL,
  `teamMemberTransferID` int(11) DEFAULT NULL,
  `leagueID` int(11) NOT NULL,
  `divisionID` int(11) NOT NULL,
  `teamID` int(11) NOT NULL,
  `userID` int(11) NOT NULL,
  `requester` tinyint(1) NOT NULL,
  `otherTeamID` int(11) DEFAULT NULL,
  `otherUserID` int(11) DEFAULT NULL,
  `transactionType` tinyint(4) NOT NULL,
  `membersBefore` varchar(512) CHARACTER SET utf8 COLLATE utf8_bin NOT NULL,
  `membersAfter` varchar(512) CHARACTER SET utf8 COLLATE utf8_bin NOT NULL,
  `createdBy` int(11) NOT NULL,
  `createdIn` datetime NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;

-- --------------------------------------------------------

--
-- Table structure for table `TeamMemberTransfers`
--

CREATE TABLE `TeamMemberTransfers` (
  `teamMemberTransferID` int(11) NOT NULL,
  `leagueID` int(11) NOT NULL,
  `divisionID` int(11) NOT NULL,
  `teamID` int(11) NOT NULL,
  `userID` int(11) NOT NULL,
  `otherTeamID` int(11) NOT NULL,
  `otherUserID` int(11) NOT NULL,
  `transferStatus` tinyint(4) NOT NULL,
  `memberKeys` varchar(512) CHARACTER SET utf8 COLLATE utf8_bin NOT NULL,
  `notes` text CHARACTER SET utf8,
  `createdBy` int(11) NOT NULL,
  `createdIn` datetime NOT NULL,
  `updatedBy` int(11) DEFAULT NULL,
  `updatedIn` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;

-- --------------------------------------------------------

--
-- Table structure for table `Teams`
--

CREATE TABLE `Teams` (
  `teamID` int(11) NOT NULL,
  `baseRealCompetitionID` int(11) NOT NULL,
  `extraRealCompetitionID` int(11) DEFAULT NULL,
  `matchDayMapKey` varchar(20) CHARACTER SET utf8 COLLATE utf8_bin DEFAULT NULL,
  `leagueID` int(11) NOT NULL,
  `divisionID` int(11) NOT NULL,
  `commissionerID` int(11) NOT NULL,
  `userID` int(11) DEFAULT NULL,
  `prevLeagueID` int(11) DEFAULT NULL,
  `nextLeagueID` int(11) DEFAULT NULL,
  `prevDivisionID` int(11) DEFAULT NULL,
  `nextDivisionID` int(11) DEFAULT NULL,
  `prevTeamID` int(11) DEFAULT NULL,
  `nextTeamID` int(11) DEFAULT NULL,
  `season` smallint(6) NOT NULL,
  `seasonNum` smallint(6) NOT NULL,
  `leagueMatches` tinyint(4) DEFAULT '0',
  `divisionMatches` tinyint(4) DEFAULT '0',
  `draftOrder` smallint(6) NOT NULL,
  `randomOrder` smallint(6) NOT NULL,
  `waiversOrder` smallint(6) NOT NULL,
  `teamName` varchar(128) CHARACTER SET utf8 NOT NULL,
  `teamAvatar` varchar(128) CHARACTER SET utf8 COLLATE utf8_bin DEFAULT NULL,
  `teamMembers` text CHARACTER SET utf8 NOT NULL,
  `draftMembers` text CHARACTER SET utf8 COLLATE utf8_bin NOT NULL,
  `membersRanking` text CHARACTER SET utf8 NOT NULL,
  `membersWaivers` text CHARACTER SET utf8 NOT NULL,
  `membersWishList` text CHARACTER SET utf8 NOT NULL,
  `franchiseWishList` text CHARACTER SET utf8 NOT NULL,
  `fantasyPoints` smallint(6) NOT NULL,
  `teamRanking` smallint(6) NOT NULL,
  `locked` tinyint(1) NOT NULL,
  `isCommissioner` tinyint(1) NOT NULL,
  `cntEPLTeam` smallint(6) NOT NULL,
  `cntPlayer` smallint(6) NOT NULL,
  `cntGoalkeeper` smallint(6) NOT NULL,
  `cntDefender` smallint(6) NOT NULL,
  `cntMidfielder` smallint(6) NOT NULL,
  `cntStriker` smallint(6) NOT NULL,
  `cntAdd` smallint(6) NOT NULL,
  `cntDrop` smallint(6) NOT NULL,
  `cntWaiver` smallint(6) NOT NULL,
  `notes` text CHARACTER SET utf8,
  `place` smallint(6) DEFAULT NULL,
  `points` smallint(6) DEFAULT NULL,
  `statusC1` tinyint(4) DEFAULT '0',
  `statusC2` tinyint(4) DEFAULT '0',
  `statusC3` tinyint(4) DEFAULT '0',
  `seedingC1` tinyint(4) NOT NULL DEFAULT '0',
  `seedingC2` tinyint(4) NOT NULL DEFAULT '0',
  `seedingC3` tinyint(4) NOT NULL DEFAULT '0',
  `createdBy` int(11) NOT NULL,
  `createdIn` datetime NOT NULL,
  `updatedBy` int(11) DEFAULT NULL,
  `updatedIn` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;

-- --------------------------------------------------------

--
-- Table structure for table `TeamStandings`
--

CREATE TABLE `TeamStandings` (
  `teamStandingID` int(11) NOT NULL,
  `leagueID` int(11) NOT NULL,
  `divisionID` int(11) NOT NULL,
  `teamID` int(11) NOT NULL,
  `userID` int(11) NOT NULL,
  `season` smallint(6) NOT NULL,
  `seasonNum` smallint(6) NOT NULL,
  `matchDayMapKey` varchar(20) CHARACTER SET utf8 COLLATE utf8_bin DEFAULT NULL,
  `realCompetitionID` int(11) NOT NULL,
  `realCompetitionMatchDay` int(11) NOT NULL,
  `competitionMatchDay` int(11) NOT NULL,
  `lastCompetitionMatchDay` int(11) DEFAULT NULL,
  `teamName` varchar(128) CHARACTER SET utf8 NOT NULL,
  `place` smallint(6) NOT NULL,
  `won` smallint(6) NOT NULL,
  `draw` smallint(6) NOT NULL,
  `lost` smallint(6) NOT NULL,
  `scoreFor` float NOT NULL,
  `scoreAgainst` float NOT NULL,
  `points` smallint(6) NOT NULL,
  `wonHome` smallint(6) NOT NULL,
  `drawHome` smallint(6) NOT NULL,
  `lostHome` smallint(6) NOT NULL,
  `scoreForHome` float NOT NULL,
  `scoreAgainstHome` float NOT NULL,
  `pointsHome` smallint(6) NOT NULL,
  `wonAway` smallint(6) NOT NULL,
  `drawAway` smallint(6) NOT NULL,
  `lostAway` smallint(6) NOT NULL,
  `scoreForAway` float NOT NULL,
  `scoreAgainstAway` float NOT NULL,
  `pointsAway` smallint(6) NOT NULL,
  `createdBy` int(11) NOT NULL,
  `createdIn` datetime NOT NULL,
  `updatedBy` int(11) DEFAULT NULL,
  `updatedIn` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;

-- --------------------------------------------------------

--
-- Table structure for table `Users`
--

CREATE TABLE `Users` (
  `userID` int(11) NOT NULL,
  `userEmail` varchar(128) CHARACTER SET utf8 NOT NULL,
  `userPassword` varchar(255) CHARACTER SET utf8 COLLATE utf8_bin NOT NULL,
  `userName` varchar(128) CHARACTER SET utf8 NOT NULL,
  `userLevel` tinyint(4) NOT NULL,
  `firstName` varchar(50) CHARACTER SET utf8 NOT NULL,
  `lastName` varchar(50) CHARACTER SET utf8 NOT NULL,
  `birthday` date NOT NULL,
  `country` varchar(50) CHARACTER SET utf8 DEFAULT NULL,
  `state` varchar(50) CHARACTER SET utf8 DEFAULT NULL,
  `city` varchar(50) CHARACTER SET utf8 DEFAULT NULL,
  `phoneNumber` varchar(15) CHARACTER SET utf8 DEFAULT NULL,
  `timeZone` varchar(20) CHARACTER SET utf8 DEFAULT NULL,
  `userAvatar` varchar(128) CHARACTER SET utf8 COLLATE utf8_bin DEFAULT NULL,
  `favoriteTeam` varchar(50) CHARACTER SET utf8 COLLATE utf8_bin DEFAULT NULL,
  `lastSignInDate` datetime DEFAULT NULL,
  `lastSignInIP` varchar(15) CHARACTER SET utf8 COLLATE utf8_bin DEFAULT NULL,
  `createdIn` datetime NOT NULL,
  `updatedIn` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `DivisionNotes`
--
ALTER TABLE `DivisionNotes`
  ADD PRIMARY KEY (`divisionNoteID`),
  ADD KEY `DivisionNotes_FK_1` (`divisionID`);

--
-- Indexes for table `Divisions`
--
ALTER TABLE `Divisions`
  ADD PRIMARY KEY (`divisionID`),
  ADD UNIQUE KEY `Divisions_K_0` (`leagueID`,`divisionType`);

--
-- Indexes for table `Leagues`
--
ALTER TABLE `Leagues`
  ADD PRIMARY KEY (`leagueID`),
  ADD UNIQUE KEY `Leagues_K_0` (`commissionerID`,`leagueName`,`season`);

--
-- Indexes for table `Lookups`
--
ALTER TABLE `Lookups`
  ADD PRIMARY KEY (`lookupID`),
  ADD UNIQUE KEY `Lookups_K_0` (`lookupNum`,`lookupKey`);

--
-- Indexes for table `MatchDaysMap`
--
ALTER TABLE `MatchDaysMap`
  ADD PRIMARY KEY (`matchDayMapID`),
  ADD UNIQUE KEY `MatchDaysMap_K_0` (`baseRealCompetitionID`,`competitionType`,`maxNumTeams`,`firstRealCompetitionMatchDay`,`matchDay`);

--
-- Indexes for table `MatchDaysStatus`
--
ALTER TABLE `MatchDaysStatus`
  ADD PRIMARY KEY (`matchDayStatusID`),
  ADD UNIQUE KEY `MatchDaysStatus_K_0` (`matchDayMapKey`,`realCompetitionID`,`realCompetitionMatchDay`);

--
-- Indexes for table `MatchDaysStatusDetail`
--
ALTER TABLE `MatchDaysStatusDetail`
  ADD PRIMARY KEY (`matchDayStatusDetailID`),
  ADD UNIQUE KEY `MatchDaysStatusDetail_1_K_1` (`matchDayMapKey`,`realCompetitionMatchDaySort`,`matchDayStatusNum`) USING BTREE,
  ADD KEY `MatchDaysStatusDetail_1_K_0` (`matchDayMapKey`,`matchDayStatusFinish`),
  ADD KEY `MatchDaysStatusDetail_1_FK_0` (`matchDayStatusID`);

--
-- Indexes for table `Matches`
--
ALTER TABLE `Matches`
  ADD PRIMARY KEY (`matchID`),
  ADD KEY `Matches_K_0` (`leagueID`,`divisionID`,`competitionType`,`competitionMatchNumber`);

--
-- Indexes for table `MatchTeams`
--
ALTER TABLE `MatchTeams`
  ADD PRIMARY KEY (`matchTeamID`),
  ADD UNIQUE KEY `MatchTeams_K_0` (`matchID`,`matchTeamNum`);

--
-- Indexes for table `ProcessStats`
--
ALTER TABLE `ProcessStats`
  ADD PRIMARY KEY (`processStatID`);

--
-- Indexes for table `RealCompetitions`
--
ALTER TABLE `RealCompetitions`
  ADD PRIMARY KEY (`realCompetitionID`);

--
-- Indexes for table `RealMatches`
--
ALTER TABLE `RealMatches`
  ADD PRIMARY KEY (`realMatchID`),
  ADD UNIQUE KEY `RealMatches_K_0` (`realCompetitionID`,`firstRealTeamUID`,`secondRealTeamUID`) USING BTREE;

--
-- Indexes for table `RealMatchPlayers`
--
ALTER TABLE `RealMatchPlayers`
  ADD PRIMARY KEY (`realMatchPlayerID`),
  ADD UNIQUE KEY `RealMatchPlayers_K_0` (`realMatchID`,`realTeamID`,`realPlayerID`);

--
-- Indexes for table `RealMatchTeams`
--
ALTER TABLE `RealMatchTeams`
  ADD PRIMARY KEY (`realMatchTeamID`),
  ADD KEY `RealMatchTeams_K_0` (`realMatchID`,`realTeamNumber`) USING BTREE;

--
-- Indexes for table `RealPlayers`
--
ALTER TABLE `RealPlayers`
  ADD PRIMARY KEY (`realPlayerID`),
  ADD UNIQUE KEY `RealPlayers_K_0` (`realCompetitionID`,`realPlayerUID`);

--
-- Indexes for table `RealStandings`
--
ALTER TABLE `RealStandings`
  ADD PRIMARY KEY (`realStandingID`),
  ADD UNIQUE KEY `RealStandings_K_0` (`realCompetitionID`,`realCompetitionMatchDay`,`realTeamMemberKey`),
  ADD UNIQUE KEY `RealStandings_K_1` (`realTeamMemberKey`,`realCompetitionID`,`realCompetitionMatchDay`);

--
-- Indexes for table `RealTeamMembers`
--
ALTER TABLE `RealTeamMembers`
  ADD PRIMARY KEY (`realTeamMemberID`),
  ADD UNIQUE KEY `RealTeamMembers_K_0` (`realTeamMemberKey`);

--
-- Indexes for table `RealTeams`
--
ALTER TABLE `RealTeams`
  ADD PRIMARY KEY (`realTeamID`),
  ADD UNIQUE KEY `RealTeams_K_0` (`realCompetitionID`,`realTeamUID`);

--
-- Indexes for table `RealVenues`
--
ALTER TABLE `RealVenues`
  ADD PRIMARY KEY (`realVenueID`),
  ADD UNIQUE KEY `RealVenues_IX01` (`realVenueUID`);

--
-- Indexes for table `Tasks`
--
ALTER TABLE `Tasks`
  ADD PRIMARY KEY (`taskID`),
  ADD KEY `Tasks_FK_01` (`parentTaskID`);

--
-- Indexes for table `TeamMemberLog`
--
ALTER TABLE `TeamMemberLog`
  ADD PRIMARY KEY (`teamMemberLogID`);

--
-- Indexes for table `TeamMemberTransfers`
--
ALTER TABLE `TeamMemberTransfers`
  ADD PRIMARY KEY (`teamMemberTransferID`);

--
-- Indexes for table `Teams`
--
ALTER TABLE `Teams`
  ADD PRIMARY KEY (`teamID`),
  ADD UNIQUE KEY `Teams_K_0` (`leagueID`,`userID`) USING BTREE,
  ADD KEY `Teams_FK_1` (`divisionID`);

--
-- Indexes for table `TeamStandings`
--
ALTER TABLE `TeamStandings`
  ADD PRIMARY KEY (`teamStandingID`),
  ADD UNIQUE KEY `TeamStandings_K_0` (`divisionID`,`competitionMatchDay`,`teamID`);

--
-- Indexes for table `Users`
--
ALTER TABLE `Users`
  ADD PRIMARY KEY (`userID`),
  ADD UNIQUE KEY `Users_K_0` (`userEmail`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `DivisionNotes`
--
ALTER TABLE `DivisionNotes`
  MODIFY `divisionNoteID` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `Divisions`
--
ALTER TABLE `Divisions`
  MODIFY `divisionID` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `Leagues`
--
ALTER TABLE `Leagues`
  MODIFY `leagueID` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `Lookups`
--
ALTER TABLE `Lookups`
  MODIFY `lookupID` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `MatchDaysMap`
--
ALTER TABLE `MatchDaysMap`
  MODIFY `matchDayMapID` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `MatchDaysStatus`
--
ALTER TABLE `MatchDaysStatus`
  MODIFY `matchDayStatusID` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `MatchDaysStatusDetail`
--
ALTER TABLE `MatchDaysStatusDetail`
  MODIFY `matchDayStatusDetailID` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `Matches`
--
ALTER TABLE `Matches`
  MODIFY `matchID` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `MatchTeams`
--
ALTER TABLE `MatchTeams`
  MODIFY `matchTeamID` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `ProcessStats`
--
ALTER TABLE `ProcessStats`
  MODIFY `processStatID` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `RealCompetitions`
--
ALTER TABLE `RealCompetitions`
  MODIFY `realCompetitionID` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `RealMatches`
--
ALTER TABLE `RealMatches`
  MODIFY `realMatchID` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `RealMatchPlayers`
--
ALTER TABLE `RealMatchPlayers`
  MODIFY `realMatchPlayerID` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `RealMatchTeams`
--
ALTER TABLE `RealMatchTeams`
  MODIFY `realMatchTeamID` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `RealPlayers`
--
ALTER TABLE `RealPlayers`
  MODIFY `realPlayerID` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `RealStandings`
--
ALTER TABLE `RealStandings`
  MODIFY `realStandingID` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `RealTeamMembers`
--
ALTER TABLE `RealTeamMembers`
  MODIFY `realTeamMemberID` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `RealTeams`
--
ALTER TABLE `RealTeams`
  MODIFY `realTeamID` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `RealVenues`
--
ALTER TABLE `RealVenues`
  MODIFY `realVenueID` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `Tasks`
--
ALTER TABLE `Tasks`
  MODIFY `taskID` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `TeamMemberLog`
--
ALTER TABLE `TeamMemberLog`
  MODIFY `teamMemberLogID` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `TeamMemberTransfers`
--
ALTER TABLE `TeamMemberTransfers`
  MODIFY `teamMemberTransferID` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `Teams`
--
ALTER TABLE `Teams`
  MODIFY `teamID` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `TeamStandings`
--
ALTER TABLE `TeamStandings`
  MODIFY `teamStandingID` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `Users`
--
ALTER TABLE `Users`
  MODIFY `userID` int(11) NOT NULL AUTO_INCREMENT;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `DivisionNotes`
--
ALTER TABLE `DivisionNotes`
  ADD CONSTRAINT `DivisionNotes_FK_1` FOREIGN KEY (`divisionID`) REFERENCES `Divisions` (`divisionID`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Constraints for table `Divisions`
--
ALTER TABLE `Divisions`
  ADD CONSTRAINT `Divisions_FK_1` FOREIGN KEY (`leagueID`) REFERENCES `Leagues` (`leagueID`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Constraints for table `MatchDaysStatusDetail`
--
ALTER TABLE `MatchDaysStatusDetail`
  ADD CONSTRAINT `MatchDaysStatusDetail_1_FK_0` FOREIGN KEY (`matchDayStatusID`) REFERENCES `MatchDaysStatus` (`matchDayStatusID`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Constraints for table `RealMatchPlayers`
--
ALTER TABLE `RealMatchPlayers`
  ADD CONSTRAINT `RealMatchPlayers_FK_1` FOREIGN KEY (`realMatchID`) REFERENCES `RealMatches` (`realMatchID`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Constraints for table `RealMatchTeams`
--
ALTER TABLE `RealMatchTeams`
  ADD CONSTRAINT `RealMatchTeams_FK_1` FOREIGN KEY (`realMatchID`) REFERENCES `RealMatches` (`realMatchID`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Constraints for table `RealStandings`
--
ALTER TABLE `RealStandings`
  ADD CONSTRAINT `RealStandings_FK_1` FOREIGN KEY (`realTeamMemberKey`) REFERENCES `RealTeamMembers` (`realTeamMemberKey`);

--
-- Constraints for table `Tasks`
--
ALTER TABLE `Tasks`
  ADD CONSTRAINT `Tasks_FK_01` FOREIGN KEY (`parentTaskID`) REFERENCES `Tasks` (`taskID`) ON DELETE CASCADE;

--
-- Constraints for table `Teams`
--
ALTER TABLE `Teams`
  ADD CONSTRAINT `Teams_FK_1` FOREIGN KEY (`divisionID`) REFERENCES `Divisions` (`divisionID`) ON DELETE CASCADE ON UPDATE CASCADE;
COMMIT;
