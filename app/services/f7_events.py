"""F7 event processing utilities."""

import xml.etree.ElementTree as ET


def add_event(events_cache: list, event: dict) -> list:
    """Add an event to the events cache with unique key generation.

    Args:
        events_cache: List of events
        event: Event dictionary with keys:
               - realPlayerUID: Player ID (can be None)
               - eventTime: Time in match
               - eventTimeStamp: Timestamp for ordering
               - eventPeriod: Period (1, 2, 'firsthalf', 'secondhalf', etc)
               - eventClass: Type (Goal, Booking, SubOff, SubOn, Assist, etc)

    Returns:
        Updated events_cache list
    """
    if event.get('realPlayerUID') is not None:
        # Normalize eventPeriod to integer
        period = str(event.get('eventPeriod', '')).strip().lower()
        if period == '1' or period == 'firsthalf':
            event['eventPeriod'] = 1
        elif period == '2' or period == 'secondhalf':
            event['eventPeriod'] = 2
        else:
            event['eventPeriod'] = None

        # Pad time to 4 digits
        event_time = event.get('eventTime', '0')
        event_time_str = "0000" + str(event_time)
        event_time_4digit = event_time_str[-4:]

        # Build unique key for event deduplication/ordering
        key = f"{event['eventPeriod']}_{event_time_4digit}_{event.get('eventTimeStamp', '')}"

        # Add class suffix for ordering within same timestamp
        event_class = event.get('eventClass', 'Other')
        if event_class == 'SubOff':
            key += '1'
        elif event_class == 'Booking':
            key += '2'
        elif event_class == 'Goal':
            key += '3'
        elif event_class == 'Assist':
            key += '4'
        elif event_class == 'SubOn':
            key += '5'
        else:
            key += '9'

        # Store key in event for reference
        event['eventKey'] = key

        events_cache.append(event)

    return events_cache


def load_booking(events_cache: list, booking_elem: ET.Element, real_team_uid: str) -> list:
    """Load a booking event (yellow/red card) from F7 XML element.

    Args:
        events_cache: List of events to append to
        booking_elem: Booking XML element
        real_team_uid: Real team UID of the team with the booking

    Returns:
        Updated events_cache list
    """
    # Extract booking information from XML
    values = {
        'realTeamUID': real_team_uid,
        'realPlayerUID': booking_elem.get('PlayerRef'),
        'eventPeriod': booking_elem.get('Period'),
        'eventTime': booking_elem.get('Time'),
        'eventNumber': booking_elem.get('EventNumber'),
        'eventTimeStamp': booking_elem.get('TimeStamp'),
        'eventType': booking_elem.get('CardType'),
        'eventClass': 'Booking',
    }

    events_cache = add_event(events_cache, values)
    return events_cache


def load_substitution(events_cache: list, substitution_elem: ET.Element, real_team_uid: str) -> list:
    """Load substitution events (player off and on) from F7 XML element.

    Args:
        events_cache: List of events to append to
        substitution_elem: Substitution XML element
        real_team_uid: Real team UID of the team with the substitution

    Returns:
        Updated events_cache list
    """
    # Create base values dictionary for substitution events
    base_values = {
        'realTeamUID': real_team_uid,
        'eventPeriod': substitution_elem.get('Period'),
        'eventTime': substitution_elem.get('Time'),
        'eventNumber': substitution_elem.get('EventNumber'),
        'eventTimeStamp': substitution_elem.get('TimeStamp'),
        'eventType': substitution_elem.get('Reason'),
    }

    # Create SubOff event (player leaving the field)
    sub_off_values = base_values.copy()
    sub_off_values['realPlayerUID'] = substitution_elem.get('SubOff')
    sub_off_values['eventClass'] = 'SubOff'
    events_cache = add_event(events_cache, sub_off_values)

    # Create SubOn event (player entering the field)
    sub_on_values = base_values.copy()
    sub_on_values['realPlayerUID'] = substitution_elem.get('SubOn')
    sub_on_values['eventClass'] = 'SubOn'
    events_cache = add_event(events_cache, sub_on_values)

    return events_cache


def load_goal(events_cache: list, goal_elem: ET.Element, real_team_uid: str) -> list:
    """Load a goal event from F7 XML element.

    Args:
        events_cache: List of events to append to
        goal_elem: Goal XML element
        real_team_uid: Real team UID of the scoring team

    Returns:
        Updated events_cache list
    """
    # Extract goal information from XML
    player_ref = goal_elem.get('PlayerRef')
    goal_type = goal_elem.get('Type')

    # Get assist player if present
    assist_elem = goal_elem.find('Assist')
    assist_player_ref = assist_elem.get('PlayerRef') if assist_elem is not None else None

    # Build goal event
    goal_values = {
        'realTeamUID': real_team_uid,
        'realPlayerUID': player_ref,
        'secondRealPlayerUID': assist_player_ref,
        'eventPeriod': goal_elem.get('Period'),
        'eventTime': goal_elem.get('Time'),
        'eventNumber': goal_elem.get('EventNumber'),
        'eventTimeStamp': goal_elem.get('TimeStamp'),
        'eventType': goal_type,
        'eventClass': 'Goal',
    }

    # Add the goal event
    events_cache = add_event(events_cache, goal_values)

    # If it's not an own goal, also add an assist event
    if goal_type != 'Own' and assist_player_ref:
        assist_values = goal_values.copy()
        assist_values['realPlayerUID'] = assist_player_ref
        assist_values['secondRealPlayerUID'] = None  # Clear the secondary player reference
        assist_values['eventClass'] = 'Assist'
        events_cache = add_event(events_cache, assist_values)

    return events_cache
