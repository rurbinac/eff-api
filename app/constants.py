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


class RealTeamMemberPositions:
    """Position/role constants for RealTeamMembers."""

    GOALKEEPER = 'Goalkeeper'
    DEFENDER = 'Defender'
    MIDFIELDER = 'Midfielder'
    STRIKER = 'Striker'


class RealTeamTypes:
    """Team type constants for RealTeamMembers."""

    EPL_TEAM = 'EPLTeam'


class DraftPositions:
    """Draft position order and name mappings for real players."""

    @staticmethod
    def get_order(position: int | str, real_position: str | None = None) -> int:
        """Calculate draft position order from position data.

        Args:
            position: Position as integer (1-5) or string name
            real_position: Real position string for mapping when position is not recognized

        Returns:
            Position order number (1-5) or 0 if not found/invalid
        """
        if isinstance(position, int):
            return position if 1 <= position <= 5 else 0

        # Handle string position
        pos = position.strip().lower() if position else None
        if not pos:
            return 0

        # Map 'forward' to striker
        if pos == 'forward':
            pos = DraftPositions.STRIKER

        # Map position names to order numbers
        position_map = {
            RealTeamMemberPositions.GOALKEEPER.lower(): 1,
            RealTeamMemberPositions.DEFENDER.lower(): 2,
            RealTeamMemberPositions.MIDFIELDER.lower(): 3,
            RealTeamMemberPositions.STRIKER.lower(): 4,
            RealTeamTypes.EPL_TEAM.lower(): 5,
        }

        # Try to find the position in the map
        if pos in position_map:
            return position_map[pos]

        # If not found and real_position is provided, try to map it
        if real_position:
            real_positions = {
                'central back': 2,
                'central defender': 2,
                'centre back': 2,
                'centre defender': 2,
                'full back': 2,
                'sweeper': 2,
                'wing back': 2,
                'attacking midfielder': 3,
                'central midfielder': 3,
                'centre midfielder': 3,
                'defensive midfielder': 3,
                'wide midfielder': 3,
                'central forward': 4,
                'centre forward': 4,
                'second striker': 4,
                'winger': 4,
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
        positions = [
            RealTeamMemberPositions.GOALKEEPER,
            RealTeamMemberPositions.DEFENDER,
            RealTeamMemberPositions.MIDFIELDER,
            RealTeamMemberPositions.STRIKER,
            RealTeamTypes.EPL_TEAM,
        ]
        return positions[order - 1] if order >= 1 and order <= 5 else None


class RealMatchStatus:
    """RealMatch status constants."""

    UNKNOWN = 0
    NOT_STARTED = 1
    PLAYING = 2
    FINISHED = 3


class RealMatchPeriod:
    """RealMatch period constants and utilities."""

    UNKNOWN = ''
    PREMATCH = 'PreMatch'
    FIRSTHALF = 'FirstHalf'
    SECONDHALF = 'SecondHalf'
    FULLTIME = 'FullTime'
    ABANDONED = 'Abandoned'
    POSTPONED = 'Postponed'

    @staticmethod
    def get_period(period) -> str:
        """Normalize and validate period string.

        Args:
            period: Period value (any type)

        Returns:
            Normalized period string or UNKNOWN if invalid
        """
        period_str = str(period).strip().lower() if period else ''

        if period_str == RealMatchPeriod.PREMATCH.lower():
            return RealMatchPeriod.PREMATCH
        elif period_str == RealMatchPeriod.FIRSTHALF.lower():
            return RealMatchPeriod.FIRSTHALF
        elif period_str == RealMatchPeriod.SECONDHALF.lower():
            return RealMatchPeriod.SECONDHALF
        elif period_str == RealMatchPeriod.FULLTIME.lower():
            return RealMatchPeriod.FULLTIME
        elif period_str == RealMatchPeriod.ABANDONED.lower():
            return RealMatchPeriod.ABANDONED
        elif period_str == RealMatchPeriod.POSTPONED.lower():
            return RealMatchPeriod.POSTPONED
        else:
            return RealMatchPeriod.UNKNOWN

    @staticmethod
    def to_match_status(period) -> int:
        """Convert period to match status.

        Args:
            period: Period value (any type)

        Returns:
            RealMatchStatus: NOT_STARTED, PLAYING, FINISHED, or UNKNOWN
        """
        normalized = RealMatchPeriod.get_period(period)

        if normalized in (RealMatchPeriod.PREMATCH, RealMatchPeriod.POSTPONED):
            return RealMatchStatus.NOT_STARTED
        elif normalized in (RealMatchPeriod.FIRSTHALF, RealMatchPeriod.SECONDHALF):
            return RealMatchStatus.PLAYING
        elif normalized in (RealMatchPeriod.FULLTIME, RealMatchPeriod.ABANDONED):
            return RealMatchStatus.FINISHED
        else:
            return RealMatchStatus.UNKNOWN

    @staticmethod
    def to_match_ended(period) -> int:
        """Determine if match is ended.

        Args:
            period: Period value (any type)

        Returns:
            1 if finished, 0 otherwise
        """
        return 1 if RealMatchPeriod.to_match_status(period) == RealMatchStatus.FINISHED else 0


class MatchConstants:
    """Match-related constants."""

    MATCHES_NONE = 0
    MATCHES_READY = 1
    MATCHES_CREATING = 2
    MATCHES_CREATED = 3

    MATCHES_DIV_RR = 2
    MATCHES_DIV_SD = 3
    MATCHES_LEA_SD = 4
