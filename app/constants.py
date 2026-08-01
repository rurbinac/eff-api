"""Application constants for lookups and configuration."""

from collections.abc import Iterator
from typing import Any, Final


class LookupConstants:
    """Lookup constants for validation against Lookups table."""

    COUNTRY_CODE: Final[int] = 1
    STATE_CODE: Final[int] = 2
    DIVISION_TYPE: Final[int] = 3
    DRAFT_TYPE: Final[int] = 4
    LEAGUE_SCORING_SYSTEM: Final[int] = 5
    USER_LEAGUE_STATUS: Final[int] = 6
    SEASON_STATUS: Final[int] = 7
    DRAFT_STATUS: Final[int] = 8
    PLAYER_POSITION: Final[int] = 9
    DIVISIONS_PER_LEAGUE: Final[int] = 10
    TEAMS_PER_DIVISION: Final[int] = 11
    LEAGUE_TYPE: Final[int] = 12
    GAME_TYPE: Final[int] = 13
    PLAYER_TRANSFER_STATUS: Final[int] = 14
    DIVISION_NOTE_TYPE: Final[int] = 15
    MATCH_STATUS: Final[int] = 16
    COMPETITION_TYPE: Final[int] = 17
    REAL_MATCH_PERIOD: Final[int] = 18
    REAL_MATCH_STATUS: Final[int] = 19
    MATCH_TEAM_MEMBER_ROLE: Final[int] = 20
    REAL_TEAM_SHORT_NAME: Final[int] = 21


class DraftConstants:
    """Draft status constants."""

    DRAFT_TIME: Final[int] = 120

    DRAFT_STATUS_HOLD: Final[int] = 0
    DRAFT_STATUS_NOT_DRAFTED: Final[int] = 1
    DRAFT_STATUS_DRAFTING: Final[int] = 2
    DRAFT_STATUS_PAUSED: Final[int] = 3
    DRAFT_STATUS_DRAFTED: Final[int] = 4

    @staticmethod
    def is_valid(value: Any) -> bool:
        return isinstance(DraftConstants.verify(value), int)

    @staticmethod
    def verify(value: Any) -> int | None:
        """Verify draft status value.

        Args:
            value: Draft status value (any type)

        Returns:
            Normalized period string or None if invalid
        """
        return _verify_int(value, DraftConstants.valid_values())

    @staticmethod
    def valid_values() -> tuple[int]:
        return (
            DraftConstants.DRAFT_STATUS_HOLD,
            DraftConstants.DRAFT_STATUS_NOT_DRAFTED,
            DraftConstants.DRAFT_STATUS_DRAFTING,
            DraftConstants.DRAFT_STATUS_PAUSED,
            DraftConstants.DRAFT_STATUS_DRAFTED,
        )

class DraftEvents:
    """Draft real-time event name constants."""

    DRAFT_START_EVENT: Final[str] = "draft-started"
    DRAFT_PAUSE_EVENT: Final[str] = "draft-paused"
    MEMBER_DRAFTED_EVENT: Final[str] = "member-drafted"
    DRAFT_MESSAGE_EVENT: Final[str] = "draft-message"

    @staticmethod
    def is_valid(value: Any) -> bool:
        return isinstance(DraftEvents.normalize(value), str)

    @staticmethod
    def normalize(value: Any) -> str | None:
        """Normalize and validate draft event string.

        Args:
            value: Draft status value (any type)

        Returns:
            Normalized period string or None if invalid
        """
        return _verify_str(value, DraftEvents.valid_values())

    @staticmethod
    def valid_values() -> tuple[str]:
        return (
            DraftEvents.DRAFT_START_EVENT,
            DraftEvents.DRAFT_PAUSE_EVENT,
            DraftEvents.MEMBER_DRAFTED_EVENT,
            DraftEvents.DRAFT_MESSAGE_EVENT,
        )


class MatchDayStatusConstants:

    WAIVERS: Final[str] = "Waivers"
    WAIVERS_SETTLE: Final[str] = "WaiversSettle"
    OPEN_WAIVERS: Final[str] = "OpenWaivers"
    OPEN_WAIVERS_SETTLE: Final[str] = "OpenWaiversSettle"
    PRE_MATCH: Final[str] = "PreMatch"
    MATCH: Final[str] = "Match"
    POST_MATCH: Final[str] = "PostMatch"

    @staticmethod
    def is_valid(value: Any) -> bool:
        return isinstance(MatchDayStatusConstants.normalize(value), str)

    @staticmethod
    def normalize(value: Any) -> str | None:
        """Normalize and validate match day status string.

        Args:
            value: Match day status value (any type)

        Returns:
            Normalized string or None if invalid
        """
        return _verify_str(value, MatchDayStatusConstants.valid_values())

    @staticmethod
    def valid_values() -> tuple[str]:
        return (
            MatchDayStatusConstants.WAIVERS,
            MatchDayStatusConstants.WAIVERS_SETTLE,
            MatchDayStatusConstants.OPEN_WAIVERS,
            MatchDayStatusConstants.OPEN_WAIVERS_SETTLE,
            MatchDayStatusConstants.PRE_MATCH,
            MatchDayStatusConstants.MATCH,
            MatchDayStatusConstants.POST_MATCH,
        )

    @staticmethod
    def boundaries() -> Iterator[tuple[str, tuple[str, str]]]:
        for key in MatchDayStatusConstants.valid_values():
            yield key, (f"start{key}", f"finish{key}")


class WaiversConstants:
    """Waiver status and configuration constants."""

    # Waiver status constants
    WAIVER_STATUS_HOLD: Final[int] = 0
    WAIVER_STATUS_NO_WAIVER: Final[int] = 1
    WAIVER_STATUS_FIRST: Final[int] = 2
    WAIVER_STATUS_SECOND: Final[int] = 3
    WAIVER_STATUS_OPEN: Final[int] = 4

    # Waiver configuration
    MAX_WAIVERS: Final[int] = 3


class RealCompetitionConstants:
    """Real competition identifiers and configuration constants."""

    SEASON_START_MONTH: Final[int] = 8

    BASE_SYMID: Final[str] = "EN_PR"
    EXTRA_SYMID: Final[str] = "EN_FA"


class DraftPositionConstants:
    """Draft position order, name mappings, and team type constants."""

    # Position constants
    GOALKEEPER: Final[str] = "Goalkeeper"
    DEFENDER: Final[str] = "Defender"
    MIDFIELDER: Final[str] = "Midfielder"
    STRIKER: Final[str] = "Striker"
    EPL_TEAM: Final[str] = "EPLTeam"

    # Aggregate position labels
    PLAYER: Final[str] = "Player"
    MEMBER: Final[str] = "Member"
    DP_UNKNOWN: Final[str] = ""

    # Min constraints
    MIN_EPL_TEAM: Final[int] = 2
    MIN_PLAYER: Final[int] = 14
    MIN_GOALKEEPER: Final[int] = 2
    MIN_DEFENDER: Final[int] = 5
    MIN_MIDFIELDER: Final[int] = 5
    MIN_STRIKER: Final[int] = 2
    MIN_MEMBER: Final[int] = MIN_PLAYER + MIN_EPL_TEAM

    # Max constraints
    MAX_EPL_TEAM: Final[int] = 2
    MAX_PLAYER: Final[int] = 17
    MAX_GOALKEEPER: Final[int] = 2
    MAX_DEFENDER: Final[int] = 7
    MAX_MIDFIELDER: Final[int] = 7
    MAX_STRIKER: Final[int] = 3
    MAX_MEMBER: Final[int] = MAX_PLAYER + MAX_EPL_TEAM

    # Lowest draft constraints
    LOWEST_EPL_TEAM: Final[int] = 1
    LOWEST_GOALKEEPER: Final[int] = 1
    LOWEST_DEFENDER: Final[int] = 4
    LOWEST_MIDFIELDER: Final[int] = 4
    LOWEST_STRIKER: Final[int] = 2

    # Position constraint limits (will be set after class definition)
    LIMITS: dict | None = None

    @staticmethod
    def is_valid(value: Any) -> bool:
        return isinstance(DraftPositionConstants.normalize(value), str)

    @staticmethod
    def normalize(value: Any) -> str | None:
        return _verify_str(value, DraftPositionConstants.valid_values())

    @staticmethod
    def valid_values() -> tuple[str]:
        return (
            DraftPositionConstants.GOALKEEPER,
            DraftPositionConstants.DEFENDER,
            DraftPositionConstants.MIDFIELDER,
            DraftPositionConstants.STRIKER,
            DraftPositionConstants.EPL_TEAM,
        )

    @staticmethod
    def get_order(position: Any, real_position: str | None = None) -> int:
        """Calculate draft position order from position data.

        Args:
            position: Position as integer (1-5) or string name
            real_position: Real position string for mapping when position is not recognized

        Returns:
            Position order number (1-5) or 0 if not found/invalid
        """
        if not position:
            return 0
        if isinstance(position, int):
            return position if 1 <= position <= 5 else 0
        if not isinstance(position, str):
            return 0
        if position.strip().lower() == "forward":
            position = DraftPositionConstants.STRIKER

        normalized = _verify_str(position, DraftPositionConstants.valid_values())
        if normalized is not None:
            return DraftPositionConstants.valid_values().index(normalized) + 1

        # If not found and real_position is provided, try to map it
        if real_position:
            real_positions = {
                "central back": 2,
                "central defender": 2,
                "centre back": 2,
                "centre defender": 2,
                "full back": 2,
                "sweeper": 2,
                "wing back": 2,
                "attacking midfielder": 3,
                "central midfielder": 3,
                "centre midfielder": 3,
                "defensive midfielder": 3,
                "wide midfielder": 3,
                "central forward": 4,
                "centre forward": 4,
                "second striker": 4,
                "winger": 4,
            }
            return real_positions.get(real_position.lower(), 0)

        return 0

    @staticmethod
    def get_position(order: int) -> str | None:
        """Get draft position string from order number.

        Args:
            order: Position order number (1-5)

        Returns:
            Position string (Goalkeeper, Defender, etc.) or None if invalid
        """
        return (
            DraftPositionConstants.valid_values()[order - 1]
            if order >= 1 and order <= 5
            else None
        )


class RealMatchStatus:
    """RealMatch status constants."""

    UNKNOWN: Final[int] = 0
    NOT_STARTED: Final[int] = 1
    PLAYING: Final[int] = 2
    FINISHED: Final[int] = 3

    @staticmethod
    def is_valid(value: Any) -> bool:
        return isinstance(RealMatchStatus.verify(value), int)

    @staticmethod
    def verify(value: Any) -> int | None:
        return _verify_int(value, RealMatchStatus.valid_values())

    @staticmethod
    def valid_values() -> tuple[int, ...]:
        return (
            RealMatchStatus.NOT_STARTED,
            RealMatchStatus.PLAYING,
            RealMatchStatus.FINISHED,
        )


class RealMatchPeriod:
    """RealMatch period constants and utilities."""

    UNKNOWN: Final[str] = ""
    PREMATCH: Final[str] = "PreMatch"
    FIRSTHALF: Final[str] = "FirstHalf"
    SECONDHALF: Final[str] = "SecondHalf"
    FULLTIME: Final[str] = "FullTime"
    ABANDONED: Final[str] = "Abandoned"
    POSTPONED: Final[str] = "Postponed"

    @staticmethod
    def is_valid(value: Any) -> bool:
        return RealMatchPeriod.normalize(value) != RealMatchPeriod.UNKNOWN

    @staticmethod
    def normalize(value: Any) -> str:
        """Normalize and validate period string.

        Args:
            value: Period value (any type)

        Returns:
            Normalized period string or UNKNOWN if invalid
        """
        return _verify_str(
            value, RealMatchPeriod.valid_values(), RealMatchPeriod.UNKNOWN
        )

    @staticmethod
    def valid_values() -> tuple[str]:
        return (
            RealMatchPeriod.PREMATCH,
            RealMatchPeriod.FIRSTHALF,
            RealMatchPeriod.SECONDHALF,
            RealMatchPeriod.FULLTIME,
            RealMatchPeriod.ABANDONED,
            RealMatchPeriod.POSTPONED,
        )

    @staticmethod
    def to_match_status(period) -> int:
        """Convert period to match status.

        Args:
            period: Period value (any type)

        Returns:
            RealMatchStatus: NOT_STARTED, PLAYING, FINISHED, or UNKNOWN
        """
        match RealMatchPeriod.normalize(period):
            case RealMatchPeriod.PREMATCH | RealMatchPeriod.POSTPONED:
                return RealMatchStatus.NOT_STARTED
            case RealMatchPeriod.FIRSTHALF | RealMatchPeriod.SECONDHALF:
                return RealMatchStatus.PLAYING
            case RealMatchPeriod.FULLTIME | RealMatchPeriod.ABANDONED:
                return RealMatchStatus.FINISHED
            case _:
                return RealMatchStatus.UNKNOWN

    @staticmethod
    def to_match_ended(period) -> int:
        """Determine if match is ended.

        Args:
            period: Period value (any type)

        Returns:
            1 if finished, 0 otherwise
        """
        return (
            1
            if RealMatchPeriod.to_match_status(period) == RealMatchStatus.FINISHED
            else 0
        )


class LineupConstants:
    MAX_SUBSTITUTES: Final[int] = 5
    VALID_FORMATIONS: Final[str] = "442,433,451"


class MatchCreationConstants:
    NONE: Final[int] = 0
    READY: Final[int] = 1
    CREATING: Final[int] = 2
    CREATED: Final[int] = 3

    @staticmethod
    def is_valid(value: Any) -> bool:
        return isinstance(MatchCreationConstants.verify(value), int)

    @staticmethod
    def verify(value: Any) -> int | None:
        return _verify_int(value, MatchCreationConstants.valid_values())

    @staticmethod
    def valid_values() -> tuple[int]:
        return (
            MatchCreationConstants.NONE,
            MatchCreationConstants.READY,
            MatchCreationConstants.CREATING,
            MatchCreationConstants.CREATED,
        )


class CompetitionTypeConstants:
    DIVISION_ROUND_ROBIN: Final[int] = 1
    DIVISION_KNOCK_OUT: Final[int] = 2
    LEAGUE_KNOCK_OUT: Final[int] = 3

    @staticmethod
    def is_valid(value: Any) -> bool:
        return isinstance(CompetitionTypeConstants.verify(value), int)

    @staticmethod
    def verify(value: Any = None) -> int | None:
        return _verify_int(value, CompetitionTypeConstants.valid_values())

    @staticmethod
    def valid_values() -> tuple[int]:
        return (
            CompetitionTypeConstants.DIVISION_ROUND_ROBIN,
            CompetitionTypeConstants.DIVISION_KNOCK_OUT,
            CompetitionTypeConstants.LEAGUE_KNOCK_OUT,
        )


class MatchStatusConstants:
    NOT_STARTED: Final[int] = 1
    PLAYING: Final[int] = 2
    FINISHED: Final[int] = 3

    @staticmethod
    def is_valid(value: Any) -> bool:
        return isinstance(MatchStatusConstants.verify(value), int)

    @staticmethod
    def verify(value: Any) -> int | None:
        return _verify_int(value, MatchStatusConstants.valid_values())

    @staticmethod
    def valid_values() -> tuple[int]:
        return (
            MatchStatusConstants.NOT_STARTED,
            MatchStatusConstants.PLAYING,
            MatchStatusConstants.FINISHED,
        )


# Initialize DraftPositionConstants.LIMITS after class definition
# This maps position names to their constraint limits (min, max, auto)
DraftPositionConstants.LIMITS = {
    DraftPositionConstants.GOALKEEPER: {
        "min": DraftPositionConstants.MIN_GOALKEEPER,
        "max": DraftPositionConstants.MAX_GOALKEEPER,
        "lowest": DraftPositionConstants.LOWEST_GOALKEEPER,
    },
    DraftPositionConstants.DEFENDER: {
        "min": DraftPositionConstants.MIN_DEFENDER,
        "max": DraftPositionConstants.MAX_DEFENDER,
        "lowest": DraftPositionConstants.LOWEST_DEFENDER,
    },
    DraftPositionConstants.MIDFIELDER: {
        "min": DraftPositionConstants.MIN_MIDFIELDER,
        "max": DraftPositionConstants.MAX_MIDFIELDER,
        "lowest": DraftPositionConstants.LOWEST_MIDFIELDER,
    },
    DraftPositionConstants.STRIKER: {
        "min": DraftPositionConstants.MIN_STRIKER,
        "max": DraftPositionConstants.MAX_STRIKER,
        "lowest": DraftPositionConstants.LOWEST_STRIKER,
    },
    DraftPositionConstants.EPL_TEAM: {
        "min": DraftPositionConstants.MIN_EPL_TEAM,
        "max": DraftPositionConstants.MAX_EPL_TEAM,
        "lowest": DraftPositionConstants.LOWEST_EPL_TEAM,
    },
    DraftPositionConstants.PLAYER: {
        "min": DraftPositionConstants.MIN_PLAYER,
        "max": DraftPositionConstants.MAX_PLAYER,
        "lowest": 0,
    },
    DraftPositionConstants.MEMBER: {
        "min": DraftPositionConstants.MIN_PLAYER + DraftPositionConstants.MIN_EPL_TEAM,
        "max": DraftPositionConstants.MAX_PLAYER + DraftPositionConstants.MAX_EPL_TEAM,
        "lowest": 0,
    },
}


def _verify_int(value: Any, values: tuple[int], default: int | None = None) -> int | None:
    """_summary_

    Args:
        value (Any): _description_
        values (tuple[int]): _description_

    Returns:
        int | None: _description_
    """
    if isinstance(value, str):
        try:
            value = int(value)
        except ValueError:
            return default
    if not isinstance(value, int):
        return default
    return value if value in values else default


def _verify_str(
    value: Any, values: tuple[str], default: str | None = None
) -> str | None:
    """_summary_

    Args:
        value (Any): _description_
        values (tuple[str]): _description_

    Returns:
        str | None: _description_
    """
    try:
        value = str(value).strip().lower()
        for v in values:
            if v.lower() == value:
                return v
    except ValueError:
        pass
    return default
