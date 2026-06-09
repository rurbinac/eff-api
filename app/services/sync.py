"""Data synchronization service for Real* tables.

Syncs redundant/denormalized data across tables to maintain consistency.
"""

from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime


class SyncService:
    """Synchronize Real* table data."""

    # Competition SYMIDs
    BASE_SYMID = 'EN_PR'
    EXTRA_SYMID = 'EN_FA'

    # Draft position constants
    DRAFT_POSITION_GOALKEEPER = 'Goalkeeper'
    DRAFT_POSITION_DEFENDER = 'Defender'
    DRAFT_POSITION_MIDFIELDER = 'Midfielder'
    DRAFT_POSITION_STRIKER = 'Striker'

    DRAFT_POSITION_TEAM = 'EPLTeam'

    @staticmethod
    def sync_real_competitions(db: Session) -> dict:
        """Sync RealCompetitions and cascade to related tables."""
        results = {
            'status': 'success',
            'queries_executed': 0,
            'rows_affected': 0,
        }

        try:
            # Query #1: Update baseID and extraID
            q1 = text("""
                UPDATE `RealCompetitions` `rc`
                   INNER JOIN `RealCompetitions` `rc_b`
                      ON `rc_b`.`realCompetitionSeasonId` = `rc`.`realCompetitionSeasonId`
                      AND `rc_b`.`realCompetitionSYMID` = :baseRealCompetitionSYMID
                   INNER JOIN `RealCompetitions` `rc_e`
                      ON `rc_e`.`realCompetitionSeasonId` = `rc`.`realCompetitionSeasonId`
                      AND `rc_e`.`realCompetitionSYMID` = :extraRealCompetitionSYMID
                   SET `rc`.`baseRealCompetitionID` = `rc_b`.`realCompetitionID`,
                       `rc`.`extraRealCompetitionID` = `rc_e`.`realCompetitionID`
            """)
            result = db.execute(q1, {
                'baseRealCompetitionSYMID': SyncService.BASE_SYMID,
                'extraRealCompetitionSYMID': SyncService.EXTRA_SYMID,
            })
            results['queries_executed'] += 1
            results['rows_affected'] += result.rowcount

            # Query #2: Update prev and next
            q2 = text("""
                UPDATE `RealCompetitions` `c`
                   LEFT OUTER JOIN `RealCompetitions` `n`
                      ON `c`.`realCompetitionSYMID` = `n`.`realCompetitionSYMID`
                      AND CAST(`c`.`realCompetitionSeasonId` AS SIGNED) + 1 = CAST(`n`.`realCompetitionSeasonId` AS SIGNED)
                   LEFT OUTER JOIN `RealCompetitions` `p`
                      ON `c`.`realCompetitionSYMID` = `p`.`realCompetitionSYMID`
                      AND CAST(`c`.`realCompetitionSeasonId` AS SIGNED) - 1 = CAST(`p`.`realCompetitionSeasonId` AS SIGNED)
                   SET `c`.`prevRealCompetitionID` = `p`.`realCompetitionID`,
                       `c`.`nextRealCompetitionID` = `n`.`realCompetitionID`
            """)
            result = db.execute(q2)
            results['queries_executed'] += 1
            results['rows_affected'] += result.rowcount

            # Query #3: Update RealTeams
            q3 = text("""
                UPDATE `RealTeams` `t`
                   LEFT OUTER JOIN `RealCompetitions` `c` ON `c`.`realCompetitionID` = `t`.`realCompetitionID`
                   SET `t`.`realCompetitionUID` = `c`.`realCompetitionUID`,
                       `t`.`realCompetitionSYMID` = `c`.`realCompetitionSYMID`,
                       `t`.`realCompetitionSeasonId` = `c`.`realCompetitionSeasonId`,
                       `t`.`baseRealCompetitionID` = `c`.`baseRealCompetitionID`,
                       `t`.`extraRealCompetitionID` = `c`.`extraRealCompetitionID`
            """)
            result = db.execute(q3)
            results['queries_executed'] += 1
            results['rows_affected'] += result.rowcount

            # Query #4: Update RealMatches
            q4 = text("""
                UPDATE `RealMatches` `m`
                   LEFT OUTER JOIN `RealCompetitions` `c` ON `c`.`realCompetitionID` = `m`.`realCompetitionID`
                   SET `m`.`realCompetitionUID` = `c`.`realCompetitionUID`,
                       `m`.`realCompetitionSYMID` = `c`.`realCompetitionSYMID`,
                       `m`.`realCompetitionSeasonId` = `c`.`realCompetitionSeasonId`,
                       `m`.`realCompetitionFirstMatchDay` = `c`.`realCompetitionFirstMatchDay`,
                       `m`.`realCompetitionLastMatchDay` = `c`.`realCompetitionLastMatchDay`,
                       `m`.`baseRealCompetitionID` = `c`.`baseRealCompetitionID`,
                       `m`.`extraRealCompetitionID` = `c`.`extraRealCompetitionID`
            """)
            result = db.execute(q4)
            results['queries_executed'] += 1
            results['rows_affected'] += result.rowcount

        except Exception as e:
            results['status'] = 'error'
            results['error'] = str(e)

        return results

    @staticmethod
    def sync_real_teams(db: Session, real_competition_id: int) -> dict:
        """Sync RealTeams and populate RealTeamMembers."""
        results = {
            'status': 'success',
            'queries_executed': 0,
            'rows_affected': 0,
        }

        try:
            # Query #1: Set base fields
            q1 = text("""
                UPDATE `RealTeams` `t`
                   LEFT OUTER JOIN `RealTeams` `t1`
                      ON `t`.`baseRealCompetitionID` = `t1`.`realCompetitionID`
                      AND `t`.`realTeamUID` = `t1`.`realTeamUID`
                   SET `t`.`baseRealTeamID` = `t1`.`realTeamID`,
                       `t`.`baseRealTeamName` = `t1`.`realTeamName`,
                       `t`.`baseRealTeamShortName` = `t1`.`realTeamShortName`,
                       `t`.`realTeamMemberKey` = CONCAT('T', `t1`.`realTeamID`),
                       `t`.`draftPosition` = :draftPosition,
                       `t`.`draftPositionOrder` = :draftPositionOrder,
                       `t`.`lastFDate` = IF(`t`.`lastF7Date` > `t`.`lastF42Date`, `t`.`lastF7Date`, `t`.`lastF42Date`)
                   WHERE `t`.`realCompetitionID` = :realCompetitionID
            """)
            result = db.execute(q1, {
                'realCompetitionID': real_competition_id,
                'draftPosition': SyncService.DRAFT_POSITION_TEAM,
                'draftPositionOrder': 5,
            })
            results['queries_executed'] += 1
            results['rows_affected'] += result.rowcount

            # Query #2: Update prev and next
            q2 = text("""
                UPDATE `RealTeams` `t`
                   LEFT OUTER JOIN `RealCompetitions` `c` ON `t`.`realCompetitionID` = `c`.`realCompetitionID`
                   LEFT OUTER JOIN `RealTeams` `t_p`
                      ON `t_p`.`realCompetitionID` = `c`.`prevRealCompetitionID`
                      AND `t_p`.`realTeamUID` = `t`.`realTeamUID`
                   LEFT OUTER JOIN `RealTeams` `t_n`
                      ON `t_n`.`realCompetitionID` = `c`.`nextRealCompetitionID`
                      AND `t_n`.`realTeamUID` = `t`.`realTeamUID`
                   SET `t`.`prevRealTeamID` = `t_p`.`realTeamID`,
                       `t`.`nextRealTeamID` = `t_n`.`realTeamID`
                   WHERE `t`.`realCompetitionID` = :realCompetitionID
            """)
            result = db.execute(q2, {'realCompetitionID': real_competition_id})
            results['queries_executed'] += 1
            results['rows_affected'] += result.rowcount

            # Query #3: Insert new RealTeams to RealTeamMembers
            q3 = text("""
                INSERT INTO `RealTeamMembers`
                    (`realTeamMemberKey`, `prevRealTeamMemberKey`, `nextRealTeamMemberKey`,
                     `baseRealCompetitionID`, `extraRealCompetitionID`,
                     `isTeam`, `isPlayer`,
                     `realTeamID`, `realTeamUID`, `realTeamName`, `realTeamShortName`,
                     `realPlayerID`, `realPlayerUID`, `firstName`, `lastName`, `knownName`,
                     `name`, `sortName`,
                     `position`, `draftPosition`, `draftPositionOrder`,
                     `birthDate`, `weight`, `height`, `jerseyNumber`,
                     `enabled`,
                     `last_ranking`, `last_timePlayed`, `last_gamePlayed`, `last_goals`, `last_assists`,
                     `last_goalsConceded`, `last_yellowCards`, `last_redCards`, `last_cleanSheet`,
                     `last_played`, `last_won`, `last_draw`, `last_lost`, `last_goalsFor`, `last_goalsAgainst`, `last_pointsL1`,
                     `ranking`,
                     `timePlayed`, `gamePlayed`, `goals`, `assists`, `goalsConceded`, `yellowCards`, `redCards`, `cleanSheet`,
                     `played`, `won`, `draw`, `lost`, `goalsFor`, `goalsAgainst`, `pointsL1`, `livePointsL1`,
                     `lastF7Date`, `lastF42Date`, `lastFDate`,
                     `createdIn`, `updatedIn`)
                SELECT `t`.`realTeamMemberKey`,
                       IF(`t`.`prevRealTeamID` IS null, null, CONCAT('T', `t`.`prevRealTeamID`)),
                       IF(`t`.`nextRealTeamID` IS null, null, CONCAT('T', `t`.`nextRealTeamID`)),
                       `t`.`baseRealCompetitionID`, `t`.`extraRealCompetitionID`,
                       1, 0,
                       `t`.`realTeamID`, `t`.`realTeamUID`, `t`.`realTeamName`, `t`.`realTeamShortName`,
                       null, null, null, null, null,
                       `t`.`realTeamName`, `t`.`realTeamName`,
                       :draftPosition, :draftPosition, :draftPositionOrder,
                       null, null, null, null,
                       1,
                       null, null, null, null, null, null, null, null, null,
                       null, null, null, null, null, null, 0,
                       `t`.`ranking`,
                       null, null, null, null, null, null, null, null,
                       0, 0, 0, 0, 0, 0, 0, 0,
                       `t`.`lastF7Date`, `t`.`lastF42Date`, `t`.`lastFDate`,
                       `t`.`createdIn`, `t`.`updatedIn`
                FROM `RealTeams` `t`
                LEFT OUTER JOIN `RealTeamMembers` `m` ON `m`.`realTeamMemberKey` = `t`.`realTeamMemberKey`
                WHERE `t`.`realTeamID` = `t`.`baseRealTeamID`
                  AND `m`.`realTeamMemberID` IS null
                  AND `t`.`realCompetitionID` = :realCompetitionID
            """)
            result = db.execute(q3, {
                'realCompetitionID': real_competition_id,
                'draftPosition': SyncService.DRAFT_POSITION_TEAM,
                'draftPositionOrder': 5,
            })
            results['queries_executed'] += 1
            results['rows_affected'] += result.rowcount

            # Query #4: Update realTeamMemberID
            q4 = text("""
                UPDATE `RealTeams` `t`
                   LEFT OUTER JOIN `RealTeamMembers` `m` ON `m`.`realTeamMemberKey` = `t`.`realTeamMemberKey`
                   SET `t`.`realTeamMemberID` = `m`.`realTeamMemberID`
                   WHERE `t`.`realCompetitionID` = :realCompetitionID
            """)
            result = db.execute(q4, {'realCompetitionID': real_competition_id})
            results['queries_executed'] += 1
            results['rows_affected'] += result.rowcount

            # Query #5: Update old RealTeams to RealTeamMembers
            q5 = text("""
                UPDATE `RealTeamMembers` `m`
                   INNER JOIN `RealTeams` `t` ON `m`.`realTeamMemberKey` = `t`.`realTeamMemberKey`
                   SET `m`.`realTeamMemberID` = `t`.`realTeamMemberID`,
                       `m`.`realTeamMemberKey` = `t`.`realTeamMemberKey`,
                       `m`.`prevRealTeamMemberKey` = IF(`t`.`prevRealTeamID` IS null, null, CONCAT('T', `t`.`prevRealTeamID`)),
                       `m`.`nextRealTeamMemberKey` = IF(`t`.`nextRealTeamID` IS null, null, CONCAT('T', `t`.`nextRealTeamID`)),
                       `m`.`baseRealCompetitionID` = `t`.`baseRealCompetitionID`,
                       `m`.`extraRealCompetitionID` = `t`.`extraRealCompetitionID`,
                       `m`.`isTeam` = 1,
                       `m`.`isPlayer` = 0,
                       `m`.`realTeamID` = `t`.`realTeamID`,
                       `m`.`realTeamUID` = `t`.`realTeamUID`,
                       `m`.`realTeamName` = `t`.`realTeamName`,
                       `m`.`realTeamShortName` = `t`.`realTeamShortName`,
                       `m`.`realPlayerID` = null,
                       `m`.`realPlayerUID` = null,
                       `m`.`firstName` = null,
                       `m`.`lastName` = null,
                       `m`.`knownName` = null,
                       `m`.`name` = `t`.`realTeamName`,
                       `m`.`sortName` = `t`.`realTeamName`,
                       `m`.`position` = :draftPosition,
                       `m`.`draftPosition` = :draftPosition,
                       `m`.`draftPositionOrder` = :draftPositionOrder,
                       `m`.`birthDate` = null,
                       `m`.`weight` = null,
                       `m`.`height` = null,
                       `m`.`jerseyNumber` = null,
                       `m`.`last_ranking` = null,
                       `m`.`last_timePlayed` = null,
                       `m`.`last_gamePlayed` = null,
                       `m`.`last_goals` = null,
                       `m`.`last_assists` = null,
                       `m`.`last_goalsConceded` = null,
                       `m`.`last_yellowCards` = null,
                       `m`.`last_redCards` = null,
                       `m`.`last_cleanSheet` = null,
                       `m`.`timePlayed` = null,
                       `m`.`gamePlayed` = null,
                       `m`.`goals` = null,
                       `m`.`assists` = null,
                       `m`.`goalsConceded` = null,
                       `m`.`yellowCards` = null,
                       `m`.`redCards` = null,
                       `m`.`cleanSheet` = null,
                       `m`.`lastF7Date` = `t`.`lastF7Date`,
                       `m`.`lastF42Date` = `t`.`lastF42Date`,
                       `m`.`lastFDate` = `t`.`lastFDate`,
                       `m`.`createdIn` = `t`.`createdIn`,
                       `m`.`updatedIn` = `t`.`updatedIn`
                   WHERE `t`.`realTeamID` = `t`.`baseRealTeamID`
                     AND `t`.`realCompetitionID` = :realCompetitionID
            """)
            result = db.execute(q5, {
                'realCompetitionID': real_competition_id,
                'draftPosition': SyncService.DRAFT_POSITION_TEAM,
                'draftPositionOrder': 5,
            })
            results['queries_executed'] += 1
            results['rows_affected'] += result.rowcount

        except Exception as e:
            results['status'] = 'error'
            results['error'] = str(e)

        return results

    # TODO: Implement sync_real_players() and sync_real_matches()
