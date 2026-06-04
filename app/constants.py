"""Application constants for lookups and configuration."""
from datetime import datetime, timedelta


class LookupNum:
    """Lookup numbers for validation against Lookups table."""

    COUNTRY_CODE = 1
    STATE_CODE = 2
    DIVISION_TYPE = 3
    DRAFT_TYPE = 4
    LEAGUE_SCORING_SYSTEM = 5
    USER_LEAGUE_STATUS = 6
    SEASON_STATUS = 7
    DRAFT_STATUS = 8
    PLAYER_POSITION = 9
    DIVISIONS_PER_LEAGUE = 10
    TEAMS_PER_DIVISION = 11
    LEAGUE_TYPE = 12
    GAME_TYPE = 13
    PLAYER_TRANSFER_STATUS = 14
    DIVISION_NOTE_TYPE = 15
    MATCH_STATUS = 16
    COMPETITION_TYPE = 17
    REAL_MATCH_PERIOD = 18
    REAL_MATCH_STATUS = 19
    MATCH_TEAM_MEMBER_ROLE = 20
    REAL_TEAM_SHORT_NAME = 21


class DraftConstants:
    """Draft and waiver status constants."""

    DRAFT_TIME = 120

    DRAFT_STATUS_HOLD = 0
    DRAFT_STATUS_NOT_DRAFTED = 1
    DRAFT_STATUS_DRAFTING = 2
    DRAFT_STATUS_PAUSED = 3
    DRAFT_STATUS_DRAFTED = 4

    WAIVER_STATUS_HOLD = 0
    WAIVER_STATUS_NO_WAIVER = 1
    WAIVER_STATUS_FIRST = 2
    WAIVER_STATUS_SECOND = 3
    WAIVER_STATUS_OPEN = 4


class MatchConstants:
    """Match-related constants."""

    MATCHES_NONE = 0
    MATCHES_READY = 1
    MATCHES_CREATING = 2
    MATCHES_CREATED = 3

    MATCHES_DIV_RR = 2
    MATCHES_DIV_SD = 3
    MATCHES_LEA_SD = 4
