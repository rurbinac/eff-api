"""F7 event processing utilities."""


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
