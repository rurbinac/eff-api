from datetime import datetime, timedelta

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.context import RequestContext
from app.services.query import QueryService

# Days added to the current datetime when searching for the next schedule template.
# Ensures we look past any match day that is already underway.
ADD_DAYS = 2


# ---------------------------------------------------------------------------
# matchDayMapKey format
# ---------------------------------------------------------------------------
# A matchDayMapKey is a comma-separated string of 2-digit zero-padded integers
# encoding up to five scheduling parameters:
#
#   Division key  (3 parts):  "RR,SS,DD"
#   League key    (5 parts):  "RR,SS,DD,LL,TT"
#
# where:
#   RR = baseRealCompetitionID (zero-padded to 2 digits)
#   SS = schedule-slot identifier (match-day sequence slot)
#   DD = division team count (e.g. 08 or 10)
#   LL = league team count / capacity tier (e.g. 08, 15, 16, 31, 32, 63)
#   TT = (reserved / additional tier)
#
# SQL LIKE wildcards: when searching, "__" (two underscores) is used in place
# of any unknown 2-character segment, since "_" matches exactly one character
# in SQL LIKE patterns.
# ---------------------------------------------------------------------------


def build_map_days_map_key(
    rcID: int,
    divMD: int | None = None,
    divCnt: int | None = None,
    leaMD: int | None = None,
    leaCnt: int | None = None,
) -> str | None:
    """Build a matchDayMapKey string from its component parts.

    Constructs one of three key formats depending on which arguments are supplied:

    - **Competition only** (no division/league args): ``"RR"``
    - **Division key** (divMD + divCnt, no league args): ``"RR,SS,DD"``
    - **League key** (all five args): ``"RR,SS,DD,LL,TT"``

    Any other combination of None/non-None arguments is invalid and returns None.
    All integers are zero-padded to 2 digits.

    Args:
        rcID: Base RealCompetitionID (required).
        divMD: Division schedule-slot (match-day sequence number).
        divCnt: Number of teams in the division (e.g. 8 or 10).
        leaMD: League schedule-slot (match-day sequence number).
        leaCnt: League capacity tier (e.g. 8, 15, 16, 31, 32, 63).

    Returns:
        The formatted matchDayMapKey string, or None for an invalid argument
        combination (e.g. divCnt supplied without divMD, or leaMD without leaCnt).
    """
    if divMD is None and divCnt is None and leaMD is None and leaCnt is None:
        return f"{rcID:02}"
    if divMD is not None and divCnt is not None and leaMD is None and leaCnt is None:
        return f"{rcID:02},{divMD:02},{divCnt:02}"
    if (
        divMD is not None
        and divCnt is not None
        and leaMD is not None
        and leaCnt is not None
    ):
        return f"{rcID:02},{divMD:02},{divCnt:02},{leaMD:02},{leaCnt:02}"
    return None


def build_division_map_days_map_key(rcID: int, divMD: int, divCnt: int) -> str | None:
    """Build a 3-part division matchDayMapKey (``"RR,SS,DD"``).

    Convenience wrapper around build_map_days_map_key for the division case.

    Args:
        rcID: Base RealCompetitionID.
        divMD: Division schedule-slot (match-day sequence number).
        divCnt: Number of teams in the division (e.g. 8 or 10).

    Returns:
        A key string such as ``"05,03,08"``.
    """
    return build_map_days_map_key(rcID, divMD, divCnt)


def build_league_map_days_map_key(
    rcID: int, divMD: int, divCnt: int, leaMD: int, leaCnt: int
) -> str | None:
    """Build a 5-part league matchDayMapKey (``"RR,SS,DD,LL,TT"``).

    Convenience wrapper around build_map_days_map_key for the league case.

    Args:
        rcID: Base RealCompetitionID.
        divMD: Division schedule-slot (match-day sequence number).
        divCnt: Number of teams in the division (e.g. 8 or 10).
        leaMD: League schedule-slot (match-day sequence number).
        leaCnt: League capacity tier (e.g. 8, 15, 16, 31, 32, 63).

    Returns:
        A key string such as ``"05,03,08,02,16"``.
    """
    return build_map_days_map_key(rcID, divMD, divCnt, leaMD, leaCnt)


def division_map_days_map_key(
    db: Session, divCnt: int, rcID: int | None = None, dt: datetime | None = None
) -> str | None:
    """Find the matchDayMapKey for a division's schedule template.

    Looks up the first upcoming MatchDaysStatus row (at least ADD_DAYS ahead)
    whose key matches the pattern ``"RR,__,DD"`` — i.e. the correct
    RealCompetition and division team-count, with any schedule-slot in between.

    Only divisions of 8 or 10 teams are supported; any other size returns None.

    Args:
        db: Database session.
        divCnt: Number of teams in the division (8 or 10).
        rcID: Base RealCompetitionID. If None, fetched from the current season
            via QueryService.get_current_base_competition.
        dt: Reference datetime for the search. Defaults to RequestContext.get_datetime().

    Returns:
        The matching matchDayMapKey string, or None if not found.
    """
    rcID = _get_rc_id(db, rcID)
    if rcID is not None:
        if dt is None:
            dt = RequestContext.get_datetime()
        if divCnt == 8 or divCnt == 10:
            return _find(db, dt, f"{rcID:02},__,{divCnt:02}")
    return None


def league_map_days_map_key(
    db: Session, leaCnt: int, key: str | None = None, dt: datetime | None = None
) -> str | None:
    """Find the matchDayMapKey for a league's schedule template.

    Extends an existing division key (or builds from scratch) with a league
    capacity tier, then looks up the first upcoming MatchDaysStatus row whose
    5-part key matches.

    League team counts are mapped to capacity tiers as follows:

    =========  ====
    leaCnt     tier
    =========  ====
    8           08
    9 - 15      15
    16          16
    17 - 31     31
    32          32
    33 - 63     63
    =========  ====

    Args:
        db: Database session.
        leaCnt: Total number of teams in the league.
        key: Optional division matchDayMapKey prefix (e.g. ``"05,03,08"``).
            If None or empty, the league key is built without a division prefix
            (a bare comma is prepended so the LIKE pattern aligns correctly).
        dt: Reference datetime for the search. Defaults to RequestContext.get_datetime().

    Returns:
        The matching matchDayMapKey string, or None if leaCnt is out of range
        or no template is found.
    """
    if dt is None:
        dt = RequestContext.get_datetime()
    key = "" if key is None else key.strip()
    if key == "":
        key += ","
    for n in [8, 16, 32]:
        if leaCnt == n:
            return _find(db, dt, f"{key}__,{n:02}")
        elif leaCnt < 2 * n:
            return _find(db, dt, f"{key}__,{2 * n - 1:02}")
    return None


def split_map_days_map_key(
    key: str | None,
) -> tuple[int | None, int | None, int | None, int | None, int | None]:
    """Parse a matchDayMapKey into its five integer components.

    Accepts 3-part (division) or 5-part (league) keys. A 3-part key is padded
    with None values at positions 3 and 4.

    Args:
        key: A matchDayMapKey string such as ``"05,03,08"`` or
            ``"05,03,08,02,16"``. None or malformed values return all-None.

    Returns:
        A 5-tuple ``(RR, SS, DD, LL, TT)`` of ints, with None for absent parts.
        Returns ``(None, None, None, None, None)`` if the key is None, has the
        wrong number of parts, or contains non-integer segments.
    """
    if key is not None:
        values = key.split(",", 6)
        if len(values) == 3 or len(values) == 5:
            try:
                values[:] = [int(x) for x in values]
                while len(values) < 5:
                    values.append(None)
                return tuple(values)
            except ValueError:
                pass
    return (None, None, None, None, None)


def split_division_map_days_map_key_div(
    key: str | None,
) -> tuple[int | None, int | None, int | None]:
    """Extract the division-level components from a matchDayMapKey.

    Returns the first three fields ``(RR, SS, DD)`` — RealCompetitionID,
    schedule-slot, and division team count — discarding any league-level parts.

    Args:
        key: A matchDayMapKey string (3- or 5-part).

    Returns:
        A 3-tuple ``(RR, SS, DD)``, with None for any missing or invalid part.
    """
    values = split_map_days_map_key(key)
    return values[:3]


def split_league_map_days_map_key(
    key: str | None,
) -> tuple[int | None, int | None, int | None]:
    """Extract the league-level components from a matchDayMapKey.

    Returns ``(RR, LL, TT)`` — RealCompetitionID and the two league-tier fields
    — skipping the division-specific middle parts (SS, DD).

    Args:
        key: A 5-part matchDayMapKey string.

    Returns:
        A 3-tuple ``(RR, LL, TT)``, with None for any missing or invalid part.
    """
    values = split_map_days_map_key(key)
    return values[:1] + values[-2:]


def _find(db: Session, dt: datetime, key: str) -> str | None:
    """Query MatchDaysStatus for the first upcoming schedule template matching key.

    Searches for the earliest active MatchDaysStatus row that:
    - is the first in its sequence (``prevActiveMatchDayStatusID IS NULL``),
    - has ``startPreMatch`` at least ADD_DAYS after ``dt``, and
    - whose ``matchDayMapKey`` matches the LIKE pattern in ``key``
      (``__`` wildcards match any 2-character segment).

    Results are ordered by ``matchDayMapKey`` ascending so the lowest-numbered
    template wins when multiple rows match.

    Args:
        db: Database session.
        dt: Reference datetime; ADD_DAYS is added before querying.
        key: SQL LIKE pattern for matchDayMapKey, e.g. ``"05,__,08"``.

    Returns:
        The matched matchDayMapKey string, or None if no row qualifies.
    """
    date = dt + timedelta(days=ADD_DAYS)
    stmt = text("""
        SELECT `matchDayMapKey`
        FROM `MatchDaysStatus`
        WHERE `active` = 1
            AND `prevActiveMatchDayStatusID` IS NULL
            AND `startPreMatch` >= :date
            AND `matchDayMapKey` LIKE :key
        ORDER BY `matchDayMapKey`
    """)
    row = db.execute(stmt, {"date": date, "key": key}).mappings().first()
    return row["matchDayMapKey"] if row else None


def _get_rc_id(db: Session, rcID: int | None = None) -> int | None:
    """Resolve a RealCompetitionID, falling back to the current season's base competition.

    Args:
        db: Database session (used only when rcID is None).
        rcID: Explicit RealCompetitionID, or None to auto-resolve.

    Returns:
        The resolved RealCompetitionID, or None if rcID is None and no base
        competition exists for the current season.
    """
    if rcID is None:
        rc = QueryService.get_current_base_competition(db)
        rcID = None if rc is None else rc.get("baseRealCompetitionID")
    return rcID
