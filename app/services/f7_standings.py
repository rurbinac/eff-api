"""F7 standings and player performance calculation."""


def process_events(players_cache: dict, events_cache: list, real_match_time: int) -> dict:
    """Process all events in chronological order to update player stats.

    Args:
        players_cache: Player cache with performance tracking fields
        events_cache: Sorted list of match events
        real_match_time: Total match time in minutes

    Returns:
        Updated players_cache with event statistics
    """
    for event in events_cache:
        event_class = event.get('eventClass')

        if event_class == 'Goal':
            players_cache = process_goal(players_cache, event)
        elif event_class == 'Assist':
            players_cache = process_assist(players_cache, event)
        elif event_class == 'SubOff':
            players_cache = process_sub_off(players_cache, event)
        elif event_class == 'SubOn':
            players_cache = process_sub_on(players_cache, event, real_match_time)
        elif event_class == 'Booking':
            players_cache = process_booking(players_cache, event)
        # Unknown event type - ignore

    return players_cache


def process_goal(players_cache: dict, event: dict) -> dict:
    """Process a goal event."""
    real_player_uid = event['realPlayerUID']

    if event.get('eventType') != 'Own':
        # Regular goal
        players_cache[real_player_uid]['goals'] += 1
        # Update clean sheet for defending team
        opposite_team_uid = players_cache[real_player_uid].get('oppositeRealTeamUID')
        if opposite_team_uid:
            players_cache = process_match_clean_sheet(players_cache, opposite_team_uid)
    else:
        # Own goal
        players_cache[real_player_uid]['ownGoals'] += 1
        # Update clean sheet for own team
        own_team_uid = players_cache[real_player_uid]['realTeamUID']
        players_cache = process_match_clean_sheet(players_cache, own_team_uid)

    return players_cache


def process_match_clean_sheet(players_cache: dict, real_team_uid: str) -> dict:
    """Process clean sheet updates when a goal is conceded."""
    for real_player_uid, player_data in players_cache.items():
        if (player_data.get('finishedGame') and
            player_data.get('realTeamUID') == real_team_uid):
            players_cache[real_player_uid]['cleanSheet'] = 0
            players_cache[real_player_uid]['goalsConceded'] += 1

    return players_cache


def process_assist(players_cache: dict, event: dict) -> dict:
    """Process an assist event."""
    real_player_uid = event['realPlayerUID']
    players_cache[real_player_uid]['assists'] += 1
    return players_cache


def process_sub_off(players_cache: dict, event: dict) -> dict:
    """Process a substitution off event."""
    real_player_uid = event['realPlayerUID']
    event_time = event.get('eventTime')

    if real_player_uid in players_cache and event_time:
        try:
            event_time = int(event_time)
            players_cache[real_player_uid]['finishedGame'] = 0
            players_cache[real_player_uid]['fullGame'] = 0
            players_cache[real_player_uid]['timeOut'] = event_time
            time_in = players_cache[real_player_uid].get('timeIn', 0)
            players_cache[real_player_uid]['timePlayed'] = event_time - time_in
        except (ValueError, TypeError):
            pass

    return players_cache


def process_sub_on(players_cache: dict, event: dict, real_match_time: int) -> dict:
    """Process a substitution on event."""
    real_player_uid = event['realPlayerUID']
    event_time = event.get('eventTime')

    if real_player_uid in players_cache and event_time:
        try:
            event_time = int(event_time)
            players_cache[real_player_uid]['finishedGame'] = 1
            players_cache[real_player_uid]['gamePlayed'] = 1
            players_cache[real_player_uid]['timeIn'] = event_time
            players_cache[real_player_uid]['timeOut'] = real_match_time
            players_cache[real_player_uid]['timePlayed'] = real_match_time - event_time
            players_cache[real_player_uid]['cleanSheet'] = 1
        except (ValueError, TypeError):
            pass

    return players_cache


def process_booking(players_cache: dict, event: dict) -> dict:
    """Process a booking event (yellow/red cards)."""
    real_player_uid = event['realPlayerUID']
    event_type = event.get('eventType')

    if real_player_uid in players_cache:
        if event_type == 'Yellow':
            players_cache[real_player_uid]['yellowCards'] += 1
        elif event_type == 'SecondYellow':
            players_cache[real_player_uid]['secondYellowCards'] += 1
            players_cache[real_player_uid]['redCards'] += 1
            # Player sent off
            players_cache = process_sub_off(players_cache, event)
        elif event_type == 'StraightRed':
            players_cache[real_player_uid]['straightRedCards'] += 1
            players_cache[real_player_uid]['redCards'] += 1
            # Player sent off
            players_cache = process_sub_off(players_cache, event)
        # Unknown booking type - ignore

    return players_cache


def calculate_player_points(players_cache: dict, split_minutes: int = 45) -> dict:
    """Calculate fantasy points for all players based on event statistics.

    Args:
        players_cache: Player cache with event statistics
        split_minutes: Threshold for split point calculation (default 45 minutes)

    Returns:
        Updated players_cache with calculated points
    """
    import math

    for player_uid, player in players_cache.items():
        players_cache[player_uid] = calculate_points(player, split_minutes)

    return players_cache


def calculate_points(player: dict, split_minutes: int) -> dict:
    """Calculate position-specific points for a player."""
    import math

    player['pointsPlayed'] = calculate_played_points(player, split_minutes)

    draft_position = player.get('draftPosition') or player.get('draftPositionOrder')

    if draft_position == 1:  # GOALKEEPER
        player['pointsGoalsAllowed'] = calculate_goals_allowed_points(player, 1)
        player['pointsCleanSheet'] = calculate_clean_sheet_points(player, split_minutes, 3, 2, 0)
        player['pointsCards'] = calculate_cards_points(player, -1, -3, -4)
        player['pointsGoals'] = calculate_goals_points(player, 8)
        player['pointsAssists'] = calculate_assists_points(player, 2)
        player['pointsOwnGoals'] = calculate_own_goals_points(player, -3)

    elif draft_position == 2:  # DEFENDER
        player['pointsGoalsAllowed'] = calculate_goals_allowed_points(player, 1)
        player['pointsCleanSheet'] = calculate_clean_sheet_points(player, split_minutes, 3, 2, 0)
        player['pointsCards'] = calculate_cards_points(player, -1, -3, -4)
        player['pointsGoals'] = calculate_goals_points(player, 7)
        player['pointsAssists'] = calculate_assists_points(player, 2)
        player['pointsOwnGoals'] = calculate_own_goals_points(player, -3)

    elif draft_position == 3:  # MIDFIELDER
        player['pointsGoalsAllowed'] = calculate_goals_allowed_points(player, 0.5)
        player['pointsCleanSheet'] = calculate_clean_sheet_points(player, split_minutes, 2, 1, 0)
        player['pointsCards'] = calculate_cards_points(player, -1, -3, -4)
        player['pointsGoals'] = calculate_goals_points(player, 6)
        player['pointsAssists'] = calculate_assists_points(player, 2)
        player['pointsOwnGoals'] = calculate_own_goals_points(player, -3)

    elif draft_position == 4:  # STRIKER
        player['pointsGoalsAllowed'] = calculate_goals_allowed_points(player, 0)
        player['pointsCleanSheet'] = calculate_clean_sheet_points(player, split_minutes, 0, 0, 0)
        player['pointsCards'] = calculate_cards_points(player, -1, -3, -4)
        player['pointsGoals'] = calculate_goals_points(player, 5)
        player['pointsAssists'] = calculate_assists_points(player, 2)
        player['pointsOwnGoals'] = calculate_own_goals_points(player, -3)

    return player


def calculate_played_points(player: dict, split_minutes: int) -> int:
    """Calculate points for time played."""
    return split_points(player, split_minutes, 3, 2, 1)


def calculate_goals_allowed_points(player: dict, factor: float) -> int:
    """Calculate negative points for goals conceded."""
    import math
    return -math.floor(factor * player.get('goalsConceded', 0))


def calculate_clean_sheet_points(player: dict, split_minutes: int,
                                  full_game: int, high: int, low: int) -> int:
    """Calculate clean sheet points based on playing time."""
    if player.get('cleanSheet'):
        return split_points(player, split_minutes, full_game, high, low)
    else:
        return 0


def calculate_cards_points(player: dict, yellow_points: int,
                           second_yellow_points: int, straight_red_points: int) -> int:
    """Calculate points based on card offenses."""
    if player.get('straightRedCards', 0) > 0:
        return straight_red_points
    elif player.get('secondYellowCards', 0) > 0:
        return second_yellow_points
    elif player.get('yellowCards', 0) > 0:
        return yellow_points
    else:
        return 0


def calculate_goals_points(player: dict, factor: int) -> int:
    """Calculate points for goals scored."""
    return factor * player.get('goals', 0)


def calculate_assists_points(player: dict, factor: int) -> int:
    """Calculate points for assists."""
    return factor * player.get('assists', 0)


def calculate_own_goals_points(player: dict, factor: int) -> int:
    """Calculate negative points for own goals."""
    return factor * player.get('ownGoals', 0)


def split_points(player: dict, split_minutes: int,
                 full_game: int, high: int, low: int) -> int:
    """Calculate split points based on playing time."""
    if player.get('fullGame'):
        return full_game
    elif player.get('timePlayed', 0) >= split_minutes:
        time_in = player.get('timeIn', 0)
        if (90 - time_in) >= split_minutes:
            return high
        else:
            return low
    elif player.get('timePlayed', 0) >= 1:
        return low
    else:
        return 0
