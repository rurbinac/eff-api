"""Standings synchronization and calculation service.

Syncs RealTeamMembers with match statistics and RealStandings data,
calculating standings, places, and rankings.
"""

from sqlalchemy.orm import Session
from sqlalchemy import text


class SyncStandingsService:
    """Synchronize standings and calculate rankings."""

    # Competition SYMIDs
    BASE_SYMID = 'EN_PR'
    EXTRA_SYMID = 'EN_FA'

    @staticmethod
    def sync_real_team_members(db: Session, real_competition_id: int) -> dict:
        """Sync RealTeamMembers with match and player data across competitions.

        Args:
            db: Database session
            real_competition_id: RealCompetitionID to sync (base or extra)

        Returns:
            Results dict with status and operation counts
        """
        results = {
            'status': 'success',
            'queries_executed': 0,
            'rows_affected': 0,
            'match_days_processed': 0,
        }

        try:
            # Step 1: Load RealCompetitions and organize by SYMID
            q_comps = text("""
                SELECT *
                FROM `RealCompetitions`
                WHERE `baseRealCompetitionID` = :realCompetitionID
                   OR `extraRealCompetitionID` = :realCompetitionID
            """)
            comp_rows = db.execute(q_comps, {'realCompetitionID': real_competition_id}).fetchall()

            # Organize competitions by SYMID
            real_comp = {}
            for row in comp_rows:
                row_dict = dict(row._mapping) if hasattr(row, '_mapping') else dict(zip(row.keys(), row))
                symid = row_dict.get('realCompetitionSYMID')
                if symid == SyncStandingsService.BASE_SYMID:
                    real_comp[SyncStandingsService.BASE_SYMID] = row_dict
                elif symid == SyncStandingsService.EXTRA_SYMID:
                    real_comp[SyncStandingsService.EXTRA_SYMID] = row_dict

            if not real_comp:
                results['status'] = 'error'
                results['error'] = 'No RealCompetitions found for given ID'
                return results

            # Step 2: Load RealTeamMembers and separate into teams/players
            base_comp_id = real_comp.get(SyncStandingsService.BASE_SYMID, {}).get('realCompetitionID')
            extra_comp_id = real_comp.get(SyncStandingsService.EXTRA_SYMID, {}).get('realCompetitionID')

            q_members = text("""
                SELECT *
                FROM `RealTeamMembers`
                WHERE `baseRealCompetitionID` = :base_id
                  AND `extraRealCompetitionID` = :extra_id
            """)
            member_rows = db.execute(q_members, {
                'base_id': base_comp_id,
                'extra_id': extra_comp_id,
            }).fetchall()

            teams = {}
            players = {}
            for row in member_rows:
                row_dict = dict(row._mapping) if hasattr(row, '_mapping') else dict(zip(row.keys(), row))
                member_key = row_dict.get('realTeamMemberKey', '')

                if member_key.startswith('T'):
                    teams[member_key] = {
                        'realTeamMemberID': row_dict.get('realTeamMemberID'),
                        'prevRealTeamMemberKey': row_dict.get('prevRealTeamMemberKey'),
                        'nextRealTeamMemberKey': row_dict.get('nextRealTeamMemberKey'),
                        'baseRealCompetitionID': real_comp[SyncStandingsService.BASE_SYMID]['realCompetitionID'],
                        'extraRealCompetitionID': real_comp[SyncStandingsService.EXTRA_SYMID]['realCompetitionID'],
                        'isTeam': 1,
                        'isPlayer': 0,
                        'realTeamID': row_dict.get('realTeamID'),
                        'realTeamUID': row_dict.get('realTeamUID'),
                        'realTeamName': row_dict.get('realTeamName'),
                        'realTeamShortName': row_dict.get('realTeamShortName'),
                        'name': row_dict.get('name'),
                        'sortName': row_dict.get('sortName'),
                        'position': row_dict.get('position'),
                        'draftPosition': row_dict.get('draftPosition'),
                        'draftPositionOrder': row_dict.get('draftPositionOrder'),
                        'enabled': row_dict.get('enabled'),
                        'matchWon': 0,
                        'matchDraw': 0,
                        'matchLost': 0,
                        'played': 0,
                        'won': 0,
                        'draw': 0,
                        'lost': 0,
                        'goalsFor': 0,
                        'goalsAgainst': 0,
                        'place': 0,
                        'playedHome': 0,
                        'wonHome': 0,
                        'drawHome': 0,
                        'lostHome': 0,
                        'goalsForHome': 0,
                        'goalsAgainstHome': 0,
                        'placeHome': 0,
                        'playedAway': 0,
                        'wonAway': 0,
                        'drawAway': 0,
                        'lostAway': 0,
                        'goalsForAway': 0,
                        'goalsAgainstAway': 0,
                        'placeAway': 0,
                        'pointsL1': 0,
                        'ranking': 0
                    }
                elif member_key.startswith('P'):
                    players[member_key] = {
                        'realTeamMemberID': row_dict.get('realTeamMemberID'),
                        'prevRealTeamMemberKey': row_dict.get('prevRealTeamMemberKey'),
                        'nextRealTeamMemberKey': row_dict.get('nextRealTeamMemberKey'),
                        'baseRealCompetitionID': row_dict.get('baseRealCompetitionID'),
                        'extraRealCompetitionID': row_dict.get('extraRealCompetitionID'),
                        'isTeam': 0,
                        'isPlayer': 1,
                        'realTeamID': row_dict.get('realTeamID'),
                        'realPlayerID': row_dict.get('realPlayerID'),
                        'realPlayerUID': row_dict.get('realPlayerUID'),
                        'firstName': row_dict.get('firstName'),
                        'lastName': row_dict.get('lastName'),
                        'knownName': row_dict.get('knownName'),
                        'name': row_dict.get('name'),
                        'sortName': row_dict.get('sortName'),
                        'position': row_dict.get('position'),
                        'draftPosition': row_dict.get('draftPosition'),
                        'draftPositionOrder': row_dict.get('draftPositionOrder'),
                        'birthDate': row_dict.get('birthDate'),
                        'weight': row_dict.get('weight'),
                        'height': row_dict.get('height'),
                        'jerseyNumber': row_dict.get('jerseyNumber'),
                        'enabled': row_dict.get('enabled'),
                        'timePlayed': 0,
                        'gamePlayed': 0,
                        'goals': 0,
                        'assists': 0,
                        'yellowCards': 0,
                        'redCards': 0,
                        'goalsConceded': 0,
                        'cleanSheet': 0,
                        'pointsL1Played': 0,
                        'pointsL1GoalsAllowed': 0,
                        'pointsL1CleanSheet': 0,
                        'pointsL1Cards': 0,
                        'pointsL1Goals': 0,
                        'pointsL1Assists': 0,
                        'pointsL1OwnGoals': 0,
                        'pointsL1': 0,
                        'ranking': 0
                    }

            # Step 3: Process each competition and match day
            for rc_key, rc in real_comp.items():
                comp_id = rc.get('realCompetitionID')
                first_match_day = rc.get('realCompetitionFirstMatchDay', 1)
                last_match_day = rc.get('realCompetitionLastMatchDay', 1)

                for match_day in range(first_match_day, last_match_day + 1):
                    # Load matches for this match day
                    q_matches = text("""
                        SELECT `m`.`realMatchID`,
                               `m`.`realMatchStatus`,
                               `m`.`realMatchDate`,
                               `m`.`realMatchTime`,
                               `mt`.`realMatchTeamID`,
                               `mt`.`realTeamMemberKey`,
                               `mt`.`realTeamShortName`,
                               `mt`.`realTeamScore`,
                               `mt`.`realTeamPoints`,
                               `mt`.`realTeamSide`
                        FROM `RealMatches` `m`
                           INNER JOIN `RealMatchTeams` `mt` ON `mt`.`realMatchID` = `m`.`realMatchID`
                        WHERE `m`.`realCompetitionID` = :comp_id
                          AND `m`.`realCompetitionMatchDay` = :match_day
                    """)
                    match_rows = db.execute(q_matches, {
                        'comp_id': comp_id,
                        'match_day': match_day,
                    }).fetchall()

                    # Organize matches by team member key, tracking opposite teams
                    opposite = {}
                    matches = {}
                    for row in match_rows:
                        row_dict = dict(row._mapping) if hasattr(row, '_mapping') else dict(zip(row.keys(), row))
                        match_id = row_dict.get('realMatchID')
                        team_member_key = row_dict.get('realTeamMemberKey')

                        # Link opposite teams
                        if match_id in opposite:
                            row_dict['op_realTeamMemberKey'] = opposite[match_id]
                            matches[opposite[match_id]]['op_realTeamMemberKey'] = team_member_key
                        else:
                            opposite[match_id] = team_member_key

                        matches[team_member_key] = row_dict

                    # Process standings in order:
                    # 1. Read existing standings and aggregate stats
                    SyncStandingsService._sync_rmt_read_rs_teams(db, rc, matches, match_day, teams)
                    SyncStandingsService._sync_rmt_read_rs_players(db, rc, matches, match_day, teams, players)

                    # 2. Calculate places and rankings
                    SyncStandingsService._sync_rmt_calc_places(teams)
                    SyncStandingsService._sync_rmt_calc_ranking(teams, players)

                    # 3. Update/insert into RealStandings
                    team_result = SyncStandingsService._sync_rmt_teams(db, rc, matches, match_day, teams)
                    results['rows_affected'] += team_result.get('rows_affected', 0)

                    player_result = SyncStandingsService._sync_rmt_players(db, rc, matches, match_day, teams, players)
                    results['rows_affected'] += player_result.get('rows_affected', 0)

                    results['match_days_processed'] += 1

        except Exception as e:
            results['status'] = 'error'
            results['error'] = str(e)

        return results

    @staticmethod
    def _sync_rmt_read_rs_teams(db: Session, rc: dict, matches: dict, match_day: int, teams: dict) -> None:
        """Read RealStandings teams data and update teams dict with calculated fields.

        Args:
            db: Database session
            rc: RealCompetition dict
            matches: Dict of matches keyed by realTeamMemberKey
            match_day: Match day number
            teams: Teams dict to update (modified in place)
        """
        comp_id = rc.get('realCompetitionID')

        # Query to get teams from RealStandings for this match day
        q = text("""
            SELECT `realStandingID`, `realTeamMemberKey`
            FROM `RealStandings`
            WHERE `realCompetitionID` = :comp_id
              AND `realCompetitionMatchDay` = :match_day
              AND LEFT(`realTeamMemberKey`, 1) = 'T'
        """)
        rows = db.execute(q, {
            'comp_id': comp_id,
            'match_day': match_day,
        }).fetchall()

        for row in rows:
            row_dict = dict(row._mapping) if hasattr(row, '_mapping') else dict(zip(row.keys(), row))
            key = row_dict.get('realTeamMemberKey')
            standing_id = row_dict.get('realStandingID')

            if key not in matches or key not in teams:
                continue

            # Extract match data
            score = matches[key].get('realTeamScore', 0)
            points = matches[key].get('realTeamPoints', 0)
            side = matches[key].get('realTeamSide', '')
            op_key = matches[key].get('op_realTeamMemberKey')
            op_score = matches[op_key].get('realTeamScore', 0) if op_key else 0

            # Calculate match result
            match_won = 1 if points == 3 else 0
            match_draw = 1 if points == 1 else 0
            match_lost = 1 if points == 0 else 0

            # Update teams dict with aggregated stats
            teams[key]['matchWon'] = match_won
            teams[key]['matchDraw'] = match_draw
            teams[key]['matchLost'] = match_lost
            teams[key]['played'] += 1
            teams[key]['won'] += match_won
            teams[key]['draw'] += match_draw
            teams[key]['lost'] += match_lost
            teams[key]['goalsFor'] += score
            teams[key]['goalsAgainst'] += op_score

            # Update home/away stats based on side
            if side:
                teams[key]['played' + side] += 1
                teams[key]['won' + side] += match_won
                teams[key]['draw' + side] += match_draw
                teams[key]['lost' + side] += match_lost
                teams[key]['goalsFor' + side] += score
                teams[key]['goalsAgainst' + side] += op_score

            # Aggregate points
            teams[key]['pointsL1'] += points

            # Store realStandingID for later updates
            teams[key]['realStandingID'] = standing_id

    @staticmethod
    def _sync_rmt_read_rs_players(db: Session, rc: dict, matches: dict, match_day: int, teams: dict, players: dict) -> None:
        """Read RealStandings players data and update players dict with match statistics.

        Args:
            db: Database session
            rc: RealCompetition dict
            matches: Dict of matches keyed by realTeamMemberKey
            match_day: Match day number
            teams: Teams dict (for reference)
            players: Players dict to update (modified in place)
        """
        comp_id = rc.get('realCompetitionID')

        # Query to get players from RealStandings for this match day
        q = text("""
            SELECT `realStandingID`,
                   `realTeamMemberKey`,
                   `matchTimePlayed`,
                   `matchGamePlayed`,
                   `matchGoals`,
                   `matchAssists`,
                   `matchYellowCards`,
                   `matchRedCards`,
                   `matchGoalsConceded`,
                   `matchCleanSheet`,
                   `matchPointsL1Played`,
                   `matchPointsL1GoalsAllowed`,
                   `matchPointsL1CleanSheet`,
                   `matchPointsL1Cards`,
                   `matchPointsL1Goals`,
                   `matchPointsL1Assists`,
                   `matchPointsL1OwnGoals`,
                   `matchPointsL1`
            FROM `RealStandings`
            WHERE `realCompetitionID` = :comp_id
              AND `realCompetitionMatchDay` = :match_day
              AND LEFT(`realTeamMemberKey`, 1) = 'P'
        """)
        rows = db.execute(q, {
            'comp_id': comp_id,
            'match_day': match_day,
        }).fetchall()

        for row in rows:
            row_dict = dict(row._mapping) if hasattr(row, '_mapping') else dict(zip(row.keys(), row))
            key = row_dict.get('realTeamMemberKey')
            standing_id = row_dict.get('realStandingID')

            if key not in players:
                continue

            # Aggregate match statistics
            players[key]['timePlayed'] += row_dict.get('matchTimePlayed', 0)
            players[key]['gamePlayed'] += row_dict.get('matchGamePlayed', 0)
            players[key]['goals'] += row_dict.get('matchGoals', 0)
            players[key]['assists'] += row_dict.get('matchAssists', 0)
            players[key]['yellowCards'] += row_dict.get('matchYellowCards', 0)
            players[key]['redCards'] += row_dict.get('matchRedCards', 0)
            players[key]['goalsConceded'] += row_dict.get('matchGoalsConceded', 0)
            players[key]['cleanSheet'] += row_dict.get('matchCleanSheet', 0)

            # Aggregate points breakdown
            players[key]['pointsL1Played'] += row_dict.get('matchPointsL1Played', 0)
            players[key]['pointsL1GoalsAllowed'] += row_dict.get('matchPointsL1GoalsAllowed', 0)
            players[key]['pointsL1CleanSheet'] += row_dict.get('matchPointsL1CleanSheet', 0)
            players[key]['pointsL1Cards'] += row_dict.get('matchPointsL1Cards', 0)
            players[key]['pointsL1Goals'] += row_dict.get('matchPointsL1Goals', 0)
            players[key]['pointsL1Assists'] += row_dict.get('matchPointsL1Assists', 0)
            players[key]['pointsL1OwnGoals'] += row_dict.get('matchPointsL1OwnGoals', 0)
            players[key]['pointsL1'] += row_dict.get('matchPointsL1', 0)

            # Store realStandingID for later updates
            players[key]['realStandingID'] = standing_id

    @staticmethod
    def _sync_rmt_calc_places(teams: dict) -> None:
        """Calculate league positions for teams across all/home/away sides.

        Args:
            teams: Teams dict to update (modified in place)
        """
        for side in ["", "Home", "Away"]:
            data = []
            for team_key, team in teams.items():
                data.append({
                    "key": team["realTeamMemberKey"],
                    "pts": team['pointsL1'],
                    "diff": team["goalsFor" + side] - team["goalsAgainst" + side],
                    "goals": team["goalsFor" + side],
                    "name": team["name"]
                })

            # Sort by: points (desc), goal difference (desc), goals (desc), name (asc)
            sorted_data = sorted(data, key=lambda x: (-x['pts'], -x['diff'], -x['goals'], x['name']))

            # Assign places
            for i, item in enumerate(sorted_data):
                teams[item["key"]]["place" + side] = i + 1

    @staticmethod
    def _sync_rmt_calc_ranking(teams: dict, players: dict) -> None:
        """Calculate overall rankings for teams and players combined.

        Args:
            teams: Teams dict to update (modified in place)
            players: Players dict to update (modified in place)
        """
        data = []

        # Add teams to ranking pool
        for team_key, team in teams.items():
            data.append({
                "key": team["realTeamMemberKey"],
                "pts": team['pointsL1'],
                "name": team["name"]
            })

        # Add players to ranking pool
        for player_key, player in players.items():
            data.append({
                "key": player["realTeamMemberKey"],
                "pts": player['pointsL1'],
                "name": player["name"]
            })

        # Sort by: points (desc), name (asc)
        sorted_data = sorted(data, key=lambda x: (-x['pts'], x['name']))

        # Assign rankings
        for i, item in enumerate(sorted_data):
            if item["key"].startswith("T"):
                teams[item["key"]]["ranking"] = i + 1
            elif item["key"].startswith("P"):
                players[item["key"]]["ranking"] = i + 1

    @staticmethod
    def _sync_rmt_teams(db: Session, rc: dict, matches: dict, match_day: int, teams: dict) -> dict:
        """Sync team members for a match day.

        Reads pre-calculated team data and updates/inserts RealStandings records.

        Args:
            db: Database session
            rc: RealCompetition dict
            matches: Dict of matches keyed by realTeamMemberKey
            match_day: Match day number
            teams: Teams dict with calculated stats (includes realStandingID if existing)

        Returns:
            Results dict with rows_affected
        """
        rows_affected = 0

        try:
            # Loop over teams and update/insert based on realStandingID
            for key, team_data in teams.items():
                if key not in matches:
                    continue

                op_key = matches[key].get('op_realTeamMemberKey')
                standing_id = team_data.get('realStandingID')

                # Build common parameters for both UPDATE and INSERT
                params = {
                    'realTeamMemberID': team_data.get('realTeamMemberID'),
                    'realTeamMemberKey': team_data.get('realTeamMemberKey'),
                    'prevRealTeamMemberKey': team_data.get('prevRealTeamMemberKey'),
                    'nextRealTeamMemberKey': team_data.get('nextRealTeamMemberKey'),
                    'realCompetitionID': rc.get('realCompetitionID'),
                    'realCompetitionUID': rc.get('realCompetitionUID'),
                    'realCompetitionSYMID': rc.get('realCompetitionSYMID'),
                    'realCompetitionSeasonId': rc.get('realCompetitionSeasonId'),
                    'realCompetitionMatchDay': match_day,
                    'realCompetitionLastMatchDay': rc.get('realCompetitionLastMatchDay'),
                    'baseRealCompetitionID': rc.get('baseRealCompetitionID'),
                    'extraRealCompetitionID': rc.get('extraRealCompetitionID'),
                    'baseMatchDay': match_day,
                    'realMatchID': matches[key].get('realMatchID'),
                    'realMatchTeamID': matches[key].get('realMatchTeamID'),
                    'realMatchDate': matches[key].get('realMatchDate'),
                    'realMatchTime': matches[key].get('realMatchTime'),
                    'realMatchStatus': matches[key].get('realMatchStatus'),
                    'realTeamID': team_data.get('realTeamID'),
                    'realTeamUID': team_data.get('realTeamUID'),
                    'realTeamName': team_data.get('realTeamName'),
                    'realTeamShortName': team_data.get('realTeamShortName'),
                    'realTeamScore': matches[key].get('realTeamScore'),
                    'realTeamSide': matches[key].get('realTeamSide'),
                    'oppositeRealTeamID': teams[op_key].get('realTeamID') if op_key else None,
                    'oppositeRealTeamUID': teams[op_key].get('realTeamUID') if op_key else None,
                    'oppositeRealTeamName': teams[op_key].get('realTeamName') if op_key else None,
                    'oppositeRealTeamShortName': teams[op_key].get('realTeamShortName') if op_key else None,
                    'oppositeRealTeamScore': matches[op_key].get('realTeamScore') if op_key else None,
                    'name': team_data.get('name'),
                    'sortName': team_data.get('sortName'),
                    'position': 5,
                    'draftPosition': 5,
                    'draftPositionOrder': 5,
                    'matchWon': team_data.get('matchWon', 0),
                    'matchDraw': team_data.get('matchDraw', 0),
                    'matchLost': team_data.get('matchLost', 0),
                    'matchPointsL1': matches[key].get('realTeamPoints', 0),
                    'livePointsL1': matches[key].get('realTeamPoints', 0),
                    'played': team_data.get('played', 0),
                    'won': team_data.get('won', 0),
                    'draw': team_data.get('draw', 0),
                    'lost': team_data.get('lost', 0),
                    'goalsFor': team_data.get('goalsFor', 0),
                    'goalsAgainst': team_data.get('goalsAgainst', 0),
                    'playedHome': team_data.get('playedHome', 0),
                    'wonHome': team_data.get('wonHome', 0),
                    'drawHome': team_data.get('drawHome', 0),
                    'lostHome': team_data.get('lostHome', 0),
                    'goalsForHome': team_data.get('goalsForHome', 0),
                    'goalsAgainstHome': team_data.get('goalsAgainstHome', 0),
                    'playedAway': team_data.get('playedAway', 0),
                    'wonAway': team_data.get('wonAway', 0),
                    'drawAway': team_data.get('drawAway', 0),
                    'lostAway': team_data.get('lostAway', 0),
                    'goalsForAway': team_data.get('goalsForAway', 0),
                    'goalsAgainstAway': team_data.get('goalsAgainstAway', 0),
                    'place': team_data.get('place', 0),
                    'placeHome': team_data.get('placeHome', 0),
                    'placeAway': team_data.get('placeAway', 0),
                    'pointsL1': team_data.get('pointsL1', 0),
                    'ranking': team_data.get('ranking', 0),
                }

                if standing_id:
                    # UPDATE existing record
                    params['standing_id'] = standing_id
                    q_update = text("""
                        UPDATE `RealStandings`
                        SET `realTeamMemberID` = :realTeamMemberID,
                            `realTeamMemberKey` = :realTeamMemberKey,
                            `prevRealTeamMemberKey` = :prevRealTeamMemberKey,
                            `nextRealTeamMemberKey` = :nextRealTeamMemberKey,
                            `realCompetitionID` = :realCompetitionID,
                            `realCompetitionUID` = :realCompetitionUID,
                            `realCompetitionSYMID` = :realCompetitionSYMID,
                            `realCompetitionSeasonId` = :realCompetitionSeasonId,
                            `realCompetitionMatchDay` = :realCompetitionMatchDay,
                            `realCompetitionLastMatchDay` = :realCompetitionLastMatchDay,
                            `baseRealCompetitionID` = :baseRealCompetitionID,
                            `extraRealCompetitionID` = :extraRealCompetitionID,
                            `isTeam` = 1,
                            `isPlayer` = 0,
                            `baseMatchDay` = :baseMatchDay,
                            `realMatchID` = :realMatchID,
                            `realMatchTeamID` = :realMatchTeamID,
                            `realMatchDate` = :realMatchDate,
                            `realMatchTime` = :realMatchTime,
                            `realMatchStatus` = :realMatchStatus,
                            `realTeamID` = :realTeamID,
                            `realTeamUID` = :realTeamUID,
                            `realTeamName` = :realTeamName,
                            `realTeamShortName` = :realTeamShortName,
                            `realTeamScore` = :realTeamScore,
                            `realTeamSide` = :realTeamSide,
                            `oppositeRealTeamID` = :oppositeRealTeamID,
                            `oppositeRealTeamUID` = :oppositeRealTeamUID,
                            `oppositeRealTeamName` = :oppositeRealTeamName,
                            `oppositeRealTeamShortName` = :oppositeRealTeamShortName,
                            `oppositeRealTeamScore` = :oppositeRealTeamScore,
                            `name` = :name,
                            `sortName` = :sortName,
                            `position` = :position,
                            `draftPosition` = :draftPosition,
                            `draftPositionOrder` = :draftPositionOrder,
                            `matchWon` = :matchWon,
                            `matchDraw` = :matchDraw,
                            `matchLost` = :matchLost,
                            `matchPointsL1` = :matchPointsL1,
                            `livePointsL1` = :livePointsL1,
                            `played` = :played,
                            `won` = :won,
                            `draw` = :draw,
                            `lost` = :lost,
                            `goalsFor` = :goalsFor,
                            `goalsAgainst` = :goalsAgainst,
                            `playedHome` = :playedHome,
                            `wonHome` = :wonHome,
                            `drawHome` = :drawHome,
                            `lostHome` = :lostHome,
                            `goalsForHome` = :goalsForHome,
                            `goalsAgainstHome` = :goalsAgainstHome,
                            `playedAway` = :playedAway,
                            `wonAway` = :wonAway,
                            `drawAway` = :drawAway,
                            `lostAway` = :lostAway,
                            `goalsForAway` = :goalsForAway,
                            `goalsAgainstAway` = :goalsAgainstAway,
                            `place` = :place,
                            `placeHome` = :placeHome,
                            `placeAway` = :placeAway,
                            `pointsL1` = :pointsL1,
                            `ranking` = :ranking,
                            `processed` = 1
                        WHERE `realStandingID` = :standing_id
                    """)
                    result = db.execute(q_update, params)
                    rows_affected += result.rowcount
                else:
                    # INSERT new record
                    q_insert = text("""
                        INSERT INTO `RealStandings`
                        (`realTeamMemberID`, `realTeamMemberKey`, `prevRealTeamMemberKey`, `nextRealTeamMemberKey`,
                         `realCompetitionID`, `realCompetitionUID`, `realCompetitionSYMID`, `realCompetitionSeasonId`,
                         `realCompetitionMatchDay`, `realCompetitionLastMatchDay`, `baseRealCompetitionID`, `extraRealCompetitionID`,
                         `isTeam`, `isPlayer`, `baseMatchDay`, `realMatchID`, `realMatchTeamID`, `realMatchDate`, `realMatchTime`,
                         `realMatchStatus`, `realTeamID`, `realTeamUID`, `realTeamName`, `realTeamShortName`, `realTeamScore`, `realTeamSide`,
                         `oppositeRealTeamID`, `oppositeRealTeamUID`, `oppositeRealTeamName`, `oppositeRealTeamShortName`, `oppositeRealTeamScore`,
                         `name`, `sortName`, `position`, `draftPosition`, `draftPositionOrder`,
                         `matchWon`, `matchDraw`, `matchLost`, `matchPointsL1`, `livePointsL1`,
                         `played`, `won`, `draw`, `lost`, `goalsFor`, `goalsAgainst`,
                         `playedHome`, `wonHome`, `drawHome`, `lostHome`, `goalsForHome`, `goalsAgainstHome`,
                         `playedAway`, `wonAway`, `drawAway`, `lostAway`, `goalsForAway`, `goalsAgainstAway`,
                         `place`, `placeHome`, `placeAway`, `pointsL1`, `ranking`, `processed`)
                        VALUES
                        (:realTeamMemberID, :realTeamMemberKey, :prevRealTeamMemberKey, :nextRealTeamMemberKey,
                         :realCompetitionID, :realCompetitionUID, :realCompetitionSYMID, :realCompetitionSeasonId,
                         :realCompetitionMatchDay, :realCompetitionLastMatchDay, :baseRealCompetitionID, :extraRealCompetitionID,
                         1, 0, :baseMatchDay, :realMatchID, :realMatchTeamID, :realMatchDate, :realMatchTime,
                         :realMatchStatus, :realTeamID, :realTeamUID, :realTeamName, :realTeamShortName, :realTeamScore, :realTeamSide,
                         :oppositeRealTeamID, :oppositeRealTeamUID, :oppositeRealTeamName, :oppositeRealTeamShortName, :oppositeRealTeamScore,
                         :name, :sortName, :position, :draftPosition, :draftPositionOrder,
                         :matchWon, :matchDraw, :matchLost, :matchPointsL1, :livePointsL1,
                         :played, :won, :draw, :lost, :goalsFor, :goalsAgainst,
                         :playedHome, :wonHome, :drawHome, :lostHome, :goalsForHome, :goalsAgainstHome,
                         :playedAway, :wonAway, :drawAway, :lostAway, :goalsForAway, :goalsAgainstAway,
                         :place, :placeHome, :placeAway, :pointsL1, :ranking, 1)
                    """)
                    result = db.execute(q_insert, params)
                    rows_affected += result.rowcount

        except Exception as e:
            return {'rows_affected': 0, 'error': str(e)}

        return {'rows_affected': rows_affected}

    @staticmethod
    def _sync_rmt_players(db: Session, rc: dict, matches: dict, match_day: int, teams: dict, players: dict) -> dict:
        """Sync player members for a match day.

        Reads pre-calculated player data and updates/inserts RealStandings records.

        Args:
            db: Database session
            rc: RealCompetition dict
            matches: Dict of matches keyed by realTeamMemberKey
            match_day: Match day number
            teams: Teams dict (for opposite team reference)
            players: Players dict with calculated stats (includes realStandingID if existing)

        Returns:
            Results dict with rows_affected
        """
        rows_affected = 0

        try:
            # Loop over players and update/insert based on realStandingID
            for key, player_data in players.items():
                # Construct team_key from player's realTeamID
                team_key = 'T' + str(player_data.get('realTeamID', ''))

                if team_key not in matches or team_key not in teams:
                    continue

                op_key = matches[team_key].get('op_realTeamMemberKey')
                standing_id = player_data.get('realStandingID')

                # Build common parameters for both UPDATE and INSERT
                params = {
                    'realTeamMemberID': player_data.get('realTeamMemberID'),
                    'realTeamMemberKey': player_data.get('realTeamMemberKey'),
                    'prevRealTeamMemberKey': player_data.get('prevRealTeamMemberKey'),
                    'nextRealTeamMemberKey': player_data.get('nextRealTeamMemberKey'),
                    'realCompetitionID': rc.get('realCompetitionID'),
                    'realCompetitionUID': rc.get('realCompetitionUID'),
                    'realCompetitionSYMID': rc.get('realCompetitionSYMID'),
                    'realCompetitionSeasonId': rc.get('realCompetitionSeasonId'),
                    'realCompetitionMatchDay': match_day,
                    'realCompetitionLastMatchDay': rc.get('realCompetitionLastMatchDay'),
                    'baseRealCompetitionID': rc.get('baseRealCompetitionID'),
                    'extraRealCompetitionID': rc.get('extraRealCompetitionID'),
                    'baseMatchDay': match_day,
                    'realMatchID': matches[team_key].get('realMatchID'),
                    'realMatchTeamID': matches[team_key].get('realMatchTeamID'),
                    'realMatchDate': matches[team_key].get('realMatchDate'),
                    'realMatchTime': matches[team_key].get('realMatchTime'),
                    'realMatchStatus': matches[team_key].get('realMatchStatus'),
                    'realTeamID': teams[team_key].get('realTeamID'),
                    'realTeamUID': teams[team_key].get('realTeamUID'),
                    'realTeamName': teams[team_key].get('realTeamName'),
                    'realTeamShortName': teams[team_key].get('realTeamShortName'),
                    'realTeamScore': teams[team_key].get('realTeamScore'),
                    'realTeamSide': teams[team_key].get('realTeamSide'),
                    'oppositeRealTeamID': teams[op_key].get('realTeamID') if op_key else None,
                    'oppositeRealTeamUID': teams[op_key].get('realTeamUID') if op_key else None,
                    'oppositeRealTeamName': teams[op_key].get('realTeamName') if op_key else None,
                    'oppositeRealTeamShortName': teams[op_key].get('realTeamShortName') if op_key else None,
                    'oppositeRealTeamScore': teams[op_key].get('realTeamScore') if op_key else None,
                    'realPlayerID': player_data.get('realPlayerID'),
                    'realPlayerUID': player_data.get('realPlayerUID'),
                    'firstName': player_data.get('firstName'),
                    'lastName': player_data.get('lastName'),
                    'knownName': player_data.get('knownName'),
                    'name': player_data.get('name'),
                    'sortName': player_data.get('sortName'),
                    'position': player_data.get('position'),
                    'draftPosition': player_data.get('draftPosition'),
                    'draftPositionOrder': player_data.get('draftPositionOrder'),
                    'timePlayed': player_data.get('timePlayed', 0),
                    'gamePlayed': player_data.get('gamePlayed', 0),
                    'goals': player_data.get('goals', 0),
                    'assists': player_data.get('assists', 0),
                    'yellowCards': player_data.get('yellowCards', 0),
                    'redCards': player_data.get('redCards', 0),
                    'goalsConceded': player_data.get('goalsConceded', 0),
                    'cleanSheet': player_data.get('cleanSheet', 0),
                    'pointsL1Played': player_data.get('pointsL1Played', 0),
                    'pointsL1GoalsAllowed': player_data.get('pointsL1GoalsAllowed', 0),
                    'pointsL1CleanSheet': player_data.get('pointsL1CleanSheet', 0),
                    'pointsL1Cards': player_data.get('pointsL1Cards', 0),
                    'pointsL1Goals': player_data.get('pointsL1Goals', 0),
                    'pointsL1Assists': player_data.get('pointsL1Assists', 0),
                    'pointsL1OwnGoals': player_data.get('pointsL1OwnGoals', 0),
                    'pointsL1': player_data.get('pointsL1', 0),
                    'livePointsL1': player_data.get('pointsL1', 0),
                    'ranking': player_data.get('ranking', 0),
                }

                if standing_id:
                    # UPDATE existing record
                    params['standing_id'] = standing_id
                    q_update = text("""
                        UPDATE `RealStandings`
                        SET `realTeamMemberID` = :realTeamMemberID,
                            `realTeamMemberKey` = :realTeamMemberKey,
                            `prevRealTeamMemberKey` = :prevRealTeamMemberKey,
                            `nextRealTeamMemberKey` = :nextRealTeamMemberKey,
                            `realCompetitionID` = :realCompetitionID,
                            `realCompetitionUID` = :realCompetitionUID,
                            `realCompetitionSYMID` = :realCompetitionSYMID,
                            `realCompetitionSeasonId` = :realCompetitionSeasonId,
                            `realCompetitionMatchDay` = :realCompetitionMatchDay,
                            `realCompetitionLastMatchDay` = :realCompetitionLastMatchDay,
                            `baseRealCompetitionID` = :baseRealCompetitionID,
                            `extraRealCompetitionID` = :extraRealCompetitionID,
                            `isTeam` = 0,
                            `isPlayer` = 1,
                            `baseMatchDay` = :baseMatchDay,
                            `realMatchID` = :realMatchID,
                            `realMatchTeamID` = :realMatchTeamID,
                            `realMatchDate` = :realMatchDate,
                            `realMatchTime` = :realMatchTime,
                            `realMatchStatus` = :realMatchStatus,
                            `realTeamID` = :realTeamID,
                            `realTeamUID` = :realTeamUID,
                            `realTeamName` = :realTeamName,
                            `realTeamShortName` = :realTeamShortName,
                            `realTeamScore` = :realTeamScore,
                            `realTeamSide` = :realTeamSide,
                            `oppositeRealTeamID` = :oppositeRealTeamID,
                            `oppositeRealTeamUID` = :oppositeRealTeamUID,
                            `oppositeRealTeamName` = :oppositeRealTeamName,
                            `oppositeRealTeamShortName` = :oppositeRealTeamShortName,
                            `oppositeRealTeamScore` = :oppositeRealTeamScore,
                            `realPlayerID` = :realPlayerID,
                            `realPlayerUID` = :realPlayerUID,
                            `firstName` = :firstName,
                            `lastName` = :lastName,
                            `knownName` = :knownName,
                            `name` = :name,
                            `sortName` = :sortName,
                            `position` = :position,
                            `draftPosition` = :draftPosition,
                            `draftPositionOrder` = :draftPositionOrder,
                            `timePlayed` = :timePlayed,
                            `gamePlayed` = :gamePlayed,
                            `goals` = :goals,
                            `assists` = :assists,
                            `yellowCards` = :yellowCards,
                            `redCards` = :redCards,
                            `goalsConceded` = :goalsConceded,
                            `cleanSheet` = :cleanSheet,
                            `pointsL1Played` = :pointsL1Played,
                            `pointsL1GoalsAllowed` = :pointsL1GoalsAllowed,
                            `pointsL1CleanSheet` = :pointsL1CleanSheet,
                            `pointsL1Cards` = :pointsL1Cards,
                            `pointsL1Goals` = :pointsL1Goals,
                            `pointsL1Assists` = :pointsL1Assists,
                            `pointsL1OwnGoals` = :pointsL1OwnGoals,
                            `pointsL1` = :pointsL1,
                            `livePointsL1` = :livePointsL1,
                            `ranking` = :ranking,
                            `processed` = 1
                        WHERE `realStandingID` = :standing_id
                    """)
                    result = db.execute(q_update, params)
                    rows_affected += result.rowcount
                else:
                    # INSERT new record
                    q_insert = text("""
                        INSERT INTO `RealStandings`
                        (`realTeamMemberID`, `realTeamMemberKey`, `prevRealTeamMemberKey`, `nextRealTeamMemberKey`,
                         `realCompetitionID`, `realCompetitionUID`, `realCompetitionSYMID`, `realCompetitionSeasonId`,
                         `realCompetitionMatchDay`, `realCompetitionLastMatchDay`, `baseRealCompetitionID`, `extraRealCompetitionID`,
                         `isTeam`, `isPlayer`, `baseMatchDay`, `realMatchID`, `realMatchTeamID`, `realMatchDate`, `realMatchTime`,
                         `realMatchStatus`, `realTeamID`, `realTeamUID`, `realTeamName`, `realTeamShortName`, `realTeamScore`, `realTeamSide`,
                         `oppositeRealTeamID`, `oppositeRealTeamUID`, `oppositeRealTeamName`, `oppositeRealTeamShortName`, `oppositeRealTeamScore`,
                         `realPlayerID`, `realPlayerUID`, `firstName`, `lastName`, `knownName`, `name`, `sortName`, `position`, `draftPosition`,
                         `draftPositionOrder`, `timePlayed`, `gamePlayed`, `goals`, `assists`, `yellowCards`, `redCards`, `goalsConceded`, `cleanSheet`,
                         `pointsL1Played`, `pointsL1GoalsAllowed`, `pointsL1CleanSheet`, `pointsL1Cards`, `pointsL1Goals`, `pointsL1Assists`,
                         `pointsL1OwnGoals`, `pointsL1`, `livePointsL1`, `ranking`, `processed`)
                        VALUES
                        (:realTeamMemberID, :realTeamMemberKey, :prevRealTeamMemberKey, :nextRealTeamMemberKey,
                         :realCompetitionID, :realCompetitionUID, :realCompetitionSYMID, :realCompetitionSeasonId,
                         :realCompetitionMatchDay, :realCompetitionLastMatchDay, :baseRealCompetitionID, :extraRealCompetitionID,
                         0, 1, :baseMatchDay, :realMatchID, :realMatchTeamID, :realMatchDate, :realMatchTime,
                         :realMatchStatus, :realTeamID, :realTeamUID, :realTeamName, :realTeamShortName, :realTeamScore, :realTeamSide,
                         :oppositeRealTeamID, :oppositeRealTeamUID, :oppositeRealTeamName, :oppositeRealTeamShortName, :oppositeRealTeamScore,
                         :realPlayerID, :realPlayerUID, :firstName, :lastName, :knownName, :name, :sortName, :position, :draftPosition,
                         :draftPositionOrder, :timePlayed, :gamePlayed, :goals, :assists, :yellowCards, :redCards, :goalsConceded, :cleanSheet,
                         :pointsL1Played, :pointsL1GoalsAllowed, :pointsL1CleanSheet, :pointsL1Cards, :pointsL1Goals, :pointsL1Assists,
                         :pointsL1OwnGoals, :pointsL1, :livePointsL1, :ranking, 1)
                    """)
                    result = db.execute(q_insert, params)
                    rows_affected += result.rowcount

        except Exception as e:
            return {'rows_affected': 0, 'error': str(e)}

        return {'rows_affected': rows_affected}

    @staticmethod
    def sync_real_standings(db: Session, real_competition_id: int) -> dict:
        """Sync RealTeamMembers with data from RealStandings.

        Updates both last season data and current season data in RealTeamMembers
        based on the last match day of each competition.

        Args:
            db: Database session
            real_competition_id: RealCompetitionID to sync (base or extra)

        Returns:
            Results dict with status and rows_affected
        """
        rows_affected = 0

        try:
            # Load RealCompetitions organized by SYMID
            real_comp = SyncStandingsService._load_real_competitions(db, real_competition_id)

            if not real_comp or SyncStandingsService.BASE_SYMID not in real_comp:
                return {
                    'status': 'error',
                    'error': 'Could not load RealCompetitions',
                    'rows_affected': 0,
                }

            base_comp_id = real_comp[SyncStandingsService.BASE_SYMID]['realCompetitionID']

            # Query #1: Update last_* fields from previous season
            q1 = text("""
                UPDATE `RealTeamMembers` `rtm`
                   LEFT OUTER JOIN `RealStandings` `rs`
                      ON `rs`.`realTeamMemberKey` = `rtm`.`prevRealTeamMemberKey`
                      AND `rs`.`realCompetitionMatchDay` = `rs`.`realCompetitionLastMatchDay`
                   SET `rtm`.`last_ranking` = `rs`.`ranking`,
                       `rtm`.`last_timePlayed` = `rs`.`timePlayed`,
                       `rtm`.`last_gamePlayed` = `rs`.`gamePlayed`,
                       `rtm`.`last_goals` = `rs`.`goals`,
                       `rtm`.`last_assists` = `rs`.`assists`,
                       `rtm`.`last_goalsConceded` = `rs`.`goalsConceded`,
                       `rtm`.`last_yellowCards` = `rs`.`yellowCards`,
                       `rtm`.`last_redCards` = `rs`.`redCards`,
                       `rtm`.`last_cleanSheet` = `rs`.`cleanSheet`,
                       `rtm`.`last_played` = `rs`.`played`,
                       `rtm`.`last_won` = `rs`.`won`,
                       `rtm`.`last_draw` = `rs`.`draw`,
                       `rtm`.`last_lost` = `rs`.`lost`,
                       `rtm`.`last_goalsFor` = `rs`.`goalsFor`,
                       `rtm`.`last_goalsAgainst` = `rs`.`goalsAgainst`,
                       `rtm`.`last_pointsL1` = `rs`.`pointsL1`
                   WHERE `rtm`.`baseRealCompetitionID` = :base_comp_id
            """)
            result = db.execute(q1, {'base_comp_id': base_comp_id})
            rows_affected += result.rowcount

            # Query #2: Update current season fields from current standings
            q2 = text("""
                UPDATE `RealTeamMembers` `rtm`
                   LEFT OUTER JOIN `RealStandings` `rs`
                      ON `rs`.`realTeamMemberKey` = `rtm`.`realTeamMemberKey`
                      AND `rs`.`realCompetitionMatchDay` = `rs`.`realCompetitionLastMatchDay`
                   SET `rtm`.`timePlayed` = `rs`.`timePlayed`,
                       `rtm`.`gamePlayed` = `rs`.`gamePlayed`,
                       `rtm`.`goals` = `rs`.`goals`,
                       `rtm`.`assists` = `rs`.`assists`,
                       `rtm`.`yellowCards` = `rs`.`yellowCards`,
                       `rtm`.`redCards` = `rs`.`redCards`,
                       `rtm`.`goalsConceded` = `rs`.`goalsConceded`,
                       `rtm`.`cleanSheet` = `rs`.`cleanSheet`,
                       `rtm`.`played` = `rs`.`played`,
                       `rtm`.`won` = `rs`.`won`,
                       `rtm`.`draw` = `rs`.`draw`,
                       `rtm`.`lost` = `rs`.`lost`,
                       `rtm`.`goalsFor` = `rs`.`goalsFor`,
                       `rtm`.`goalsAgainst` = `rs`.`goalsAgainst`,
                       `rtm`.`pointsL1` = `rs`.`pointsL1`,
                       `rtm`.`livePointsL1` = `rs`.`livePointsL1`,
                       `rtm`.`ranking` = `rs`.`ranking`
                   WHERE `rtm`.`baseRealCompetitionID` = :base_comp_id
            """)
            result = db.execute(q2, {'base_comp_id': base_comp_id})
            rows_affected += result.rowcount

            return {
                'status': 'success',
                'rows_affected': rows_affected,
            }

        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'rows_affected': 0,
            }

    @staticmethod
    def _load_real_competitions(db: Session, real_competition_id: int) -> dict:
        """Load RealCompetitions organized by SYMID.

        Args:
            db: Database session
            real_competition_id: RealCompetitionID (base or extra)

        Returns:
            Dict with BASE_SYMID and EXTRA_SYMID keys, or empty dict if not found
        """
        q = text("""
            SELECT *
            FROM `RealCompetitions`
            WHERE `baseRealCompetitionID` = :realCompetitionID
               OR `extraRealCompetitionID` = :realCompetitionID
        """)
        rows = db.execute(q, {'realCompetitionID': real_competition_id}).fetchall()

        real_comp = {}
        for row in rows:
            row_dict = dict(row._mapping) if hasattr(row, '_mapping') else dict(zip(row.keys(), row))
            symid = row_dict.get('realCompetitionSYMID')
            if symid == SyncStandingsService.BASE_SYMID:
                real_comp[SyncStandingsService.BASE_SYMID] = row_dict
            elif symid == SyncStandingsService.EXTRA_SYMID:
                real_comp[SyncStandingsService.EXTRA_SYMID] = row_dict

        return real_comp
