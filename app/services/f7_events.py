"""F7 event processing utilities."""

import xml.etree.ElementTree as ET


def load_booking(
    events_cache: list, booking_elem: ET.Element, real_team_uid: str
) -> None:
    """Load a booking event (yellow/red card) from F7 XML element."""
    _add_event(
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


def load_substitution(
    events_cache: list, substitution_elem: ET.Element, real_team_uid: str
) -> None:
    """Load substitution events (player off and on) from F7 XML element."""
    base = {
        "realTeamUID": real_team_uid,
        "eventPeriod": substitution_elem.get("Period"),
        "eventTime": substitution_elem.get("Time"),
        "eventNumber": substitution_elem.get("EventNumber"),
        "eventTimeStamp": substitution_elem.get("TimeStamp"),
        "eventType": substitution_elem.get("Reason"),
    }

    # SubOff — player leaving the field
    _add_event(
        events_cache,
        {
            **base,
            "realPlayerUID": substitution_elem.get("SubOff"),
            "eventClass": "SubOff",
        },
    )

    # SubOn — player entering the field
    _add_event(
        events_cache,
        {
            **base,
            "realPlayerUID": substitution_elem.get("SubOn"),
            "eventClass": "SubOn",
        },
    )


def load_goal(events_cache: list, goal_elem: ET.Element, real_team_uid: str) -> None:
    """Load a goal (and optional assist) event from F7 XML element."""
    player_ref = goal_elem.get("PlayerRef")
    goal_type = goal_elem.get("Type")

    assist_elem = goal_elem.find("Assist")
    assist_player_ref = (
        assist_elem.get("PlayerRef") if assist_elem is not None else None
    )

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
    _add_event(events_cache, goal_event)

    # Add the assist event (not for own goals)
    if goal_type != "Own" and assist_player_ref:
        _add_event(
            events_cache,
            {
                **goal_event,
                "realPlayerUID": assist_player_ref,
                "secondRealPlayerUID": None,
                "eventClass": "Assist",
            },
        )


def _add_event(events_cache: list, event: dict) -> None:
    """Add an event to the events cache with unique key generation."""
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
