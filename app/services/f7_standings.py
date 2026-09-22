"""F7 standings and player performance calculation."""

import math

from app.constants import DraftPositionConstants


def process_events(
    players_cache: dict, events_cache: list, real_match_time: int
) -> dict:
    """Process all events in chronological order to update player stats.

    Args:
        players_cache: Player cache with performance tracking fields
        events_cache: Sorted list of match events
        real_match_time: Total match time in minutes

    Returns:
        Updated players_cache with event statistics
    """
    for event in events_cache:
        event_class = event.get("eventClass")

        if event_class == "Goal":
            _process_goal(players_cache, event)
        elif event_class == "Assist":
            _process_assist(players_cache, event)
        elif event_class == "SubOff":
            _process_sub_off(players_cache, event)
        elif event_class == "SubOn":
            _process_sub_on(players_cache, event, real_match_time)
        elif event_class == "Booking":
            _process_booking(players_cache, event)
        # Unknown event type - ignore

    return players_cache


def calc_player_points(players_cache: dict, split_minutes: int = 45) -> dict:
    """Calculate fantasy points for all players based on event statistics.

    Args:
        players_cache: Player cache with event statistics
        split_minutes: Threshold for split point calculation (default 45 minutes)

    Returns:
        Updated players_cache with calculated points
    """
    for player in players_cache.values():
        _calc_points(player, split_minutes)

    return players_cache


def _process_goal(players_cache: dict, event: dict) -> None:
    """Process a goal event."""
    real_player_uid = event["realPlayerUID"]

    if event.get("eventType") != "Own":
        players_cache[real_player_uid]["matchGoals"] += 1
        opposite_team_uid = players_cache[real_player_uid].get("oppositeRealTeamUID")
        if opposite_team_uid:
            _process_match_clean_sheet(players_cache, opposite_team_uid)
    else:
        players_cache[real_player_uid]["_ownGoals"] += 1
        own_team_uid = players_cache[real_player_uid]["realTeamUID"]
        _process_match_clean_sheet(players_cache, own_team_uid)


def _process_match_clean_sheet(players_cache: dict, real_team_uid: str) -> None:
    """Process clean sheet updates when a goal is conceded."""
    for real_player_uid, player_data in players_cache.items():
        if (
            player_data.get("_finishedGame")
            and player_data.get("realTeamUID") == real_team_uid
        ):
            players_cache[real_player_uid]["matchCleanSheet"] = 0
            players_cache[real_player_uid]["matchGoalsConceded"] += 1


def _process_assist(players_cache: dict, event: dict) -> None:
    """Process an assist event."""
    real_player_uid = event["realPlayerUID"]
    players_cache[real_player_uid]["matchAssists"] += 1


def _process_sub_off(players_cache: dict, event: dict) -> None:
    """Process a substitution off event."""
    real_player_uid = event["realPlayerUID"]
    event_time = event.get("eventTime")

    if real_player_uid in players_cache and event_time:
        try:
            event_time = int(event_time)
            players_cache[real_player_uid]["_finishedGame"] = 0
            players_cache[real_player_uid]["_fullGame"] = 0
            players_cache[real_player_uid]["_timeOut"] = event_time
            time_in = players_cache[real_player_uid].get("_timeIn", 0)
            players_cache[real_player_uid]["matchTimePlayed"] = event_time - time_in
        except (ValueError, TypeError):
            pass


def _process_sub_on(players_cache: dict, event: dict, real_match_time: int) -> None:
    """Process a substitution on event."""
    real_player_uid = event["realPlayerUID"]
    event_time = event.get("eventTime")

    if real_player_uid in players_cache and event_time:
        try:
            event_time = int(event_time)
            players_cache[real_player_uid]["_finishedGame"] = 1
            players_cache[real_player_uid]["matchGamePlayed"] = 1
            players_cache[real_player_uid]["_timeIn"] = event_time
            players_cache[real_player_uid]["_timeOut"] = real_match_time
            players_cache[real_player_uid]["matchTimePlayed"] = real_match_time - event_time
            players_cache[real_player_uid]["matchCleanSheet"] = 1
        except (ValueError, TypeError):
            pass


def _process_booking(players_cache: dict, event: dict) -> None:
    """Process a booking event (yellow/red cards)."""
    real_player_uid = event["realPlayerUID"]
    event_type = event.get("eventType")

    if real_player_uid in players_cache:
        if event_type == "Yellow":
            players_cache[real_player_uid]["matchYellowCards"] += 1
        elif event_type == "SecondYellow":
            players_cache[real_player_uid]["_secondYellowCards"] += 1
            players_cache[real_player_uid]["matchRedCards"] += 1
            _process_sub_off(players_cache, event)
        elif event_type == "StraightRed":
            players_cache[real_player_uid]["_straightRedCards"] += 1
            players_cache[real_player_uid]["matchRedCards"] += 1
            _process_sub_off(players_cache, event)
        # Unknown booking type - ignore


def _calc_points(player: dict, split_minutes: int) -> None:
    """Calculate position-specific points for a player."""
    player["matchPointsL1Played"] = _calc_played_points(player, split_minutes)

    match player.get("draftPosition"):
        case DraftPositionConstants.GOALKEEPER:
            player["matchPointsL1GoalsAllowed"] = _calc_goals_allowed_points(player, 1)
            player["matchPointsL1CleanSheet"] = _calc_clean_sheet_points(
                player, split_minutes, 3, 2, 0
            )
            player["matchPointsL1Cards"] = _calc_cards_points(player, -1, -3, -4)
            player["matchPointsL1Goals"] = _calc_goals_points(player, 8)
            player["matchPointsL1Assists"] = _calc_matchAssists_points(player, 2)
            player["matchPointsL1OwnGoals"] = _calc_own_goals_points(player, -3)

        case DraftPositionConstants.DEFENDER:
            player["matchPointsL1GoalsAllowed"] = _calc_goals_allowed_points(player, 1)
            player["matchPointsL1CleanSheet"] = _calc_clean_sheet_points(
                player, split_minutes, 3, 2, 0
            )
            player["matchPointsL1Cards"] = _calc_cards_points(player, -1, -3, -4)
            player["matchPointsL1Goals"] = _calc_goals_points(player, 7)
            player["matchPointsL1Assists"] = _calc_matchAssists_points(player, 2)
            player["matchPointsL1OwnGoals"] = _calc_own_goals_points(player, -3)

        case DraftPositionConstants.MIDFIELDER:
            player["matchPointsL1GoalsAllowed"] = _calc_goals_allowed_points(player, 0.5)
            player["matchPointsL1CleanSheet"] = _calc_clean_sheet_points(
                player, split_minutes, 2, 1, 0
            )
            player["matchPointsL1Cards"] = _calc_cards_points(player, -1, -3, -4)
            player["matchPointsL1Goals"] = _calc_goals_points(player, 6)
            player["matchPointsL1Assists"] = _calc_matchAssists_points(player, 2)
            player["matchPointsL1OwnGoals"] = _calc_own_goals_points(player, -3)

        case DraftPositionConstants.STRIKER:
            player["matchPointsL1GoalsAllowed"] = _calc_goals_allowed_points(player, 0)
            player["matchPointsL1CleanSheet"] = _calc_clean_sheet_points(
                player, split_minutes, 0, 0, 0
            )
            player["matchPointsL1Cards"] = _calc_cards_points(player, -1, -3, -4)
            player["matchPointsL1Goals"] = _calc_goals_points(player, 5)
            player["matchPointsL1Assists"] = _calc_matchAssists_points(player, 2)
            player["matchPointsL1OwnGoals"] = _calc_own_goals_points(player, -3)

        case _:
            player["matchPointsL1GoalsAllowed"] = 0
            player["matchPointsL1CleanSheet"] = 0
            player["matchPointsL1Cards"] = 0
            player["matchPointsL1Goals"] = 0
            player["matchPointsL1Assists"] = 0
            player["matchPointsL1OwnGoals"] = 0


def _calc_played_points(player: dict, split_minutes: int) -> int:
    """Calculate points for time played."""
    return _split_points(player, split_minutes, 3, 2, 1)


def _calc_goals_allowed_points(player: dict, factor: float) -> int:
    """Calculate negative points for goals conceded."""
    return -math.floor(factor * player.get("matchGoalsConceded", 0))


def _calc_clean_sheet_points(
    player: dict, split_minutes: int, full_game: int, high: int, low: int
) -> int:
    """Calculate clean sheet points based on playing time."""
    if player.get("matchCleanSheet"):
        return _split_points(player, split_minutes, full_game, high, low)
    else:
        return 0


def _calc_cards_points(
    player: dict,
    yellow_points: int,
    second_yellow_points: int,
    straight_red_points: int,
) -> int:
    """Calculate points based on card offenses."""
    if player.get("_straightRedCards", 0) > 0:
        return straight_red_points
    elif player.get("_secondYellowCards", 0) > 0:
        return second_yellow_points
    elif player.get("matchYellowCards", 0) > 0:
        return yellow_points
    else:
        return 0


def _calc_goals_points(player: dict, factor: int) -> int:
    """Calculate points for goals scored."""
    return factor * player.get("matchGoals", 0)


def _calc_matchAssists_points(player: dict, factor: int) -> int:
    """Calculate points for matchAssists."""
    return factor * player.get("matchAssists", 0)


def _calc_own_goals_points(player: dict, factor: int) -> int:
    """Calculate negative points for own goals."""
    return factor * player.get("_ownGoals", 0)


def _split_points(
    player: dict, split_minutes: int, full_game: int, high: int, low: int
) -> int:
    """Calculate split points based on playing time."""
    if player.get("_fullGame"):
        return full_game
    elif player.get("matchTimePlayed", 0) >= split_minutes:
        time_in = player.get("_timeIn", 0)
        if (90 - time_in) >= split_minutes:
            return high
        else:
            return low
    elif player.get("matchTimePlayed", 0) >= 1:
        return low
    else:
        return 0
