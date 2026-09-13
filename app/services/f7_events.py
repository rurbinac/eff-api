"""F7 event processing utilities."""

import xml.etree.ElementTree as ET


def add_event(events_cache: list, event: dict) -> list:
    """Add an event to the events cache with unique key generation.

    Args:
        events_cache: List of events
        event: Event dictionary with keys:
               - realPlayerUID: Player UID (can be None)
               - eventTime: Time in match
               - eventTimeStamp: Timestamp for ordering
               - eventPeriod: Period (1, 2, 'firsthalf', 'secondhalf', etc)
               - eventClass: Type (Goal, Booking, SubOff, SubOn, Assist, etc)

    Returns:
        Updated events_cache list
    """
    if event.get("realPlayerUID") is not None:
        # Normalize eventPeriod to integer
        period = str(event.get("eventPeriod", "")).strip().lower()
        if period == "1" or period == "firsthalf":
            event["eventPeriod"] = 1
        elif period == "2" or period == "secondhalf":
            event["eventPeriod"] = 2
        else:
            event["eventPeriod"] = None

        # Pad time to 4 digits
        event_time = event.get("eventTime", "0")
        event_time_4digit = ("0000" + str(event_time))[-4:]

        # Build unique sort/dedup key (internal — not a DB column)
        key = f"{event['eventPeriod']}_{event_time_4digit}_{event.get('eventTimeStamp', '')}"

        # Add class suffix for deterministic ordering within the same timestamp
        event_class = event.get("eventClass", "Other")
        if event_class == "SubOff":
            key += "1"
        elif event_class == "Booking":
            key += "2"
        elif event_class == "Goal":
            key += "3"
        elif event_class == "Assist":
            key += "4"
        elif event_class == "SubOn":
            key += "5"
        else:
            key += "9"

        event["eventKey"] = key
        events_cache.append(event)

    return events_cache


def load_booking(events_cache: list, booking_elem: ET.Element, real_team_uid: str) -> list:
    """Load a booking event (yellow/red card) from F7 XML element.

    Args:
        events_cache: List of events to append to
        booking_elem: Booking XML element
        real_team_uid: UID of the team with the booking

    Returns:
        Updated events_cache list
    """
    events_cache = add_event(
        events_cache,
        {
            "realTeamUID": real_team_uid,
            "realPlayerUID": booking_elem.get("PlayerRef"),
            "eventPeriod": booking_elem.get("Period"),
            "eventTime": booking_elem.get("Time"),
            "eventNumber": booking_elem.get("EventNumber"),
            "eventTimeStamp": booking_elem.get("TimeStamp"),
            "eventType": booking_elem.get("CardType"),
            "eventClass": "Booking",
        },
    )
    return events_cache


def load_substitution(
    events_cache: list, substitution_elem: ET.Element, real_team_uid: str
) -> list:
    """Load substitution events (player off and on) from F7 XML element.

    Args:
        events_cache: List of events to append to
        substitution_elem: Substitution XML element
        real_team_uid: UID of the team with the substitution

    Returns:
        Updated events_cache list
    """
    base = {
        "realTeamUID": real_team_uid,
        "eventPeriod": substitution_elem.get("Period"),
        "eventTime": substitution_elem.get("Time"),
        "eventNumber": substitution_elem.get("EventNumber"),
        "eventTimeStamp": substitution_elem.get("TimeStamp"),
        "eventType": substitution_elem.get("Reason"),
    }

    # SubOff — player leaving the field
    events_cache = add_event(
        events_cache,
        {**base, "realPlayerUID": substitution_elem.get("SubOff"), "eventClass": "SubOff"},
    )

    # SubOn — player entering the field
    events_cache = add_event(
        events_cache,
        {**base, "realPlayerUID": substitution_elem.get("SubOn"), "eventClass": "SubOn"},
    )

    return events_cache


def load_goal(events_cache: list, goal_elem: ET.Element, real_team_uid: str) -> list:
    """Load a goal (and optional assist) event from F7 XML element.

    Args:
        events_cache: List of events to append to
        goal_elem: Goal XML element
        real_team_uid: UID of the scoring team

    Returns:
        Updated events_cache list
    """
    player_ref = goal_elem.get("PlayerRef")
    goal_type = goal_elem.get("Type")

    assist_elem = goal_elem.find("Assist")
    assist_player_ref = assist_elem.get("PlayerRef") if assist_elem is not None else None

    goal_event = {
        "realTeamUID": real_team_uid,
        "realPlayerUID": player_ref,
        "secondRealPlayerUID": assist_player_ref,
        "eventPeriod": goal_elem.get("Period"),
        "eventTime": goal_elem.get("Time"),
        "eventNumber": goal_elem.get("EventNumber"),
        "eventTimeStamp": goal_elem.get("TimeStamp"),
        "eventType": goal_type,
        "eventClass": "Goal",
    }
    events_cache = add_event(events_cache, goal_event)

    # Add the assist event (not for own goals)
    if goal_type != "Own" and assist_player_ref:
        events_cache = add_event(
            events_cache,
            {
                **goal_event,
                "realPlayerUID": assist_player_ref,
                "secondRealPlayerUID": None,
                "eventClass": "Assist",
            },
        )

    return events_cache
