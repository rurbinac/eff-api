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


def calculate_player_points(players_cache: dict) -> dict:
    """Calculate fantasy points for all players.

    TODO: Implement points calculation based on:
    - pointsGoals: goals scored
    - pointsAssists: assists provided
    - pointsCards: yellow/red cards penalty
    - pointsCleanSheet: clean sheet bonus
    - pointsOwnGoals: own goals penalty
    - pointsGoalsAllowed: goals conceded penalty
    - pointsPlayed: minutes played bonus

    Args:
        players_cache: Player cache with event statistics

    Returns:
        Updated players_cache with calculated points
    """
    # TODO: User will provide the points calculation logic
    return players_cache
