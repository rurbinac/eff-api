"""
Authorization guard functions.

Two layers:
  - user_*(...)  → bool  — check membership/ownership, return True/False.
  - require_*(...) → None — raise HTTP 403 if the check fails (handles None user_id too).

Usage in a handler:
    from app.guards import require_team_owner, user_in_division

    require_team_owner(db, current_user, team_id)           # raises 403 or continues
    if user_in_division(db, current_user, division_id): ... # branch on membership
"""

from typing import Any, TypeVar

from sqlalchemy import RowMapping
from sqlalchemy.orm import Session, aliased
from sqlmodel import SQLModel

_T = TypeVar("_T", bound=SQLModel)

from app.constants import TeamMemberTransfersStatusConstants
from app.exceptions import (
    NotACommissionerException,
    NotAMemberException,
    NotFoundException,
    NotYourTeamException,
    RequiredValueException,
    UnauthorizedException,
)
from app.models import Division, League, Team, TeamMemberTransfers
from app.utils.rtm_keys import KeyGroups, Keys
from app.utils.scalars import parse_int, parse_pos_int, to_int

# ---------------------------------------------------------------------------
# Bool checks
# ---------------------------------------------------------------------------


def user_owns_team(
    db: Session,
    user_id: int,
    *,
    team_id: int | None = None,
    team: Team | RowMapping | dict | None = None,
) -> bool:
    """True if the user is the owner of the given team."""
    if team:
        return _get_value(team, "userID") == user_id
    if team_id is None:
        raise ValueError("user_owns_team requires team_id or team")
    return (
        db.query(Team).filter(Team.teamID == team_id, Team.userID == user_id).first()
    ) is not None


def user_in_division(
    db: Session,
    user_id: int,
    *,
    division_id: int | None = None,
    division: Division | RowMapping | dict | None = None,
    team_id: int | None = None,
    team: Team | RowMapping | dict | None = None,
) -> bool:
    """True if the user has a team in the given division.

    The division can be identified by ``division_id`` or ``team_id``
    (the division that team belongs to).  Raises ``ValueError`` if
    neither is provided.
    """
    if division:
        if user_id == _get_value(division, "commissionerID"):
            return True
        division_id = _get_value(division, "divisionID")
    if team:
        if user_id in (_get_value(team, "userID"), _get_value(team, "commissionerID")):
            return True
        division_id = _get_value(team, "divisionID")
    if division_id:
        return (
            db.query(Team)
            .filter(Team.divisionID == division_id, Team.userID == user_id)
            .first()
        ) is not None
    if team_id:
        return user_in_division(db, user_id, team=db.get(Team, team_id))
    raise ValueError("user_in_division requires division_id, or team_id")


def user_in_league(
    db: Session,
    user_id: int,
    *,
    league_id: int | None = None,
    league: League | RowMapping | dict | None = None,
    division_id: int | None = None,
    division: Division | RowMapping | dict | None = None,
    team_id: int | None = None,
    team: Team | RowMapping | dict | None = None,
) -> bool:
    """True if the user has a team in the given league.

    The league can be identified by ``league_id``, ``division_id``, or
    ``team_id`` — first non-None wins.  Raises ``ValueError`` if none
    of the three is provided.
    """
    if league:
        if user_id == _get_value(league, "commissionerID"):
            return True
        league_id = _get_value(league, "leagueID")
    if division:
        if user_id == _get_value(division, "commissionerID"):
            return True
        league_id = _get_value(division, "leagueID")
    if team:
        if user_id in (_get_value(team, "userID"), _get_value(team, "commissionerID")):
            return True
        league_id = _get_value(team, "leagueID")
    if league_id:
        return (
            db.query(Team)
            .filter(Team.leagueID == league_id, Team.userID == user_id)
            .first()
        ) is not None
    if division_id:
        return user_in_league(db, user_id, division=db.get(Division, division_id))
    if team_id:
        return user_in_league(db, user_id, team=db.get(Team, team_id))
    raise ValueError("user_in_league requires league_id, division_id, or team_id")


def user_is_commissioner(
    db: Session,
    user_id: int,
    *,
    league_id: int | None = None,
    league: League | RowMapping | dict | None = None,
    division_id: int | None = None,
    division: Division | RowMapping | dict | None = None,
    team_id: int | None = None,
    team: Team | RowMapping | dict | None = None,
) -> bool:
    """True if the user is a commissioner of any division of a league.

    A user qualifies if they are the league commissioner (Division.commissionerID)
    or if they have a team in the division with isCommissioner set to True.

    The division can be identified by ``division_id``, ``team_id`` (resolves to
    that team's division), or ``league_id`` (any division in that league).
    Raises ``ValueError`` if none of the three is provided.
    """
    if team:
        if user_id == _get_value(team, "commissionerID"):
            return True
        if user_id == _get_value(team, "userID") and _get_value(team, "isCommissioner"):
            return True
        return user_is_commissioner(db, user_id, league_id=_get_value(team, "leagueID"))
    if division:
        if user_id == _get_value(division, "commissionerID"):
            return True
        return user_is_commissioner(
            db, user_id, league_id=_get_value(division, "leagueID")
        )
    if league:
        if user_id == _get_value(league, "commissionerID"):
            return True
        return user_is_commissioner(
            db, user_id, league_id=_get_value(league, "leagueID")
        )
    if team_id:
        tm1, tm2 = aliased(Team), aliased(Team)
        user_team = (
            db.query(tm1)
            .join(tm2, tm1.leagueID == tm2.leagueID)
            .filter(tm1.userID == user_id, tm2.teamID == team_id)
            .first()
        )
        return user_is_commissioner(db, user_id, team=user_team)
    if division_id:
        user_team = (
            db.query(Team)
            .join(Division, Team.leagueID == Division.leagueID)
            .filter(Team.userID == user_id, Division.divisionID == division_id)
            .first()
        )
        return user_is_commissioner(db, user_id, team=user_team)
    if league_id:
        user_team = (
            db.query(Team)
            .filter(Team.leagueID == league_id, Team.userID == user_id)
            .first()
        )
        return user_is_commissioner(db, user_id, team=user_team)
    raise ValueError(
        "user_is_commissioner requires league_id, division_id, team_id, league, division or team"
    )


def user_is_division_commissioner(
    db: Session,
    user_id: int,
    *,
    division_id: int | None = None,
    division: Division | RowMapping | dict | None = None,
    team_id: int | None = None,
    team: Team | RowMapping | dict | None = None,
) -> bool:
    """True if the user is a commissioner of the given division.

    A user qualifies if they are the league commissioner (Division.commissionerID)
    or if they have a team in the division with isCommissioner set to True.

    The division can be identified by ``division_id``, ``team_id`` (resolves to
    that team's division), or ``league_id`` (any division in that league).
    Raises ``ValueError`` if none of the three is provided.
    """
    if team:
        if user_id == _get_value(team, "commissionerID"):
            return True
        if user_id == _get_value(team, "userID") and _get_value(team, "isCommissioner"):
            return True
        return user_is_division_commissioner(
            db, user_id, division_id=_get_value(team, "divisionID")
        )
    if division:
        if user_id == _get_value(division, "commissionerID"):
            return True
        return user_is_division_commissioner(
            db, user_id, division_id=_get_value(division, "divisionID")
        )
    if team_id:
        tm1, tm2 = aliased(Team), aliased(Team)
        user_team = (
            db.query(tm1)
            .join(tm2, tm1.divisionID == tm2.divisionID)
            .filter(tm1.userID == user_id, tm2.teamID == team_id)
            .first()
        )
        return user_is_division_commissioner(db, user_id, team=user_team)
    if division_id:
        user_team = (
            db.query(Team)
            .filter(Team.divisionID == division_id, Team.userID == user_id)
            .first()
        )
        return user_is_division_commissioner(db, user_id, team=user_team)
    raise ValueError(
        "user_is_division_commissioner requires division_id, team_id, division or team"
    )


def user_is_league_commissioner(
    db: Session,
    user_id: int,
    *,
    league_id: int | None = None,
    league: League | RowMapping | dict | None = None,
    division_id: int | None = None,
    division: Division | RowMapping | dict | None = None,
    team_id: int | None = None,
    team: Team | RowMapping | dict | None = None,
) -> bool:
    """True if the user is the commissioner of the given league.

    The league can be identified by a pre-fetched object or its id:
    ``team`` / ``team_id``, ``division`` / ``division_id``, or
    ``league`` / ``league_id`` — checked in that order, first non-None wins.
    Raises ``ValueError`` if none is provided.

    Because commissionerID is propagated from League down to Division and Team,
    any of these records answers the question without an extra join.
    """
    if team:
        return user_id == _get_value(team, "commissionerID")
    if division:
        return user_id == _get_value(division, "commissionerID")
    if league:
        return user_id == _get_value(league, "commissionerID")
    if team_id:
        return user_is_league_commissioner(db, user_id, team=db.get(Team, team_id))
    if division_id:
        return user_is_league_commissioner(
            db, user_id, division=db.get(Division, division_id)
        )
    if league_id:
        return user_is_league_commissioner(
            db, user_id, league=db.get(League, league_id)
        )
    raise ValueError(
        "user_is_league_commissioner requires league_id, division_id, team_id, league, division or team"
    )


# ---------------------------------------------------------------------------
# Raising variants — accept int | None so callers skip the None check
# ---------------------------------------------------------------------------


def require_authentication(current_user: int | None) -> None:
    if current_user is None:
        raise UnauthorizedException()


def require_value(
    value, value_name: str | None = None, context: str | None = None
) -> None:
    failed = False
    if value is None:
        failed = True
    elif isinstance(value, (list, dict, tuple)):
        failed = len(value) == 0
    elif not isinstance(value, (int, float)):
        failed = (value if isinstance(value, str) else str(value)).strip() == ""
    if failed:
        raise RequiredValueException(value_name, context)
    return value


def require_int(
    value,
    value_name: str | None = None,
    context: str | None = None,
    not_empty: bool = True,
) -> int:
    try:
        val = parse_int(value)
        if val is None and not_empty:
            raise RequiredValueException(value_name, context)
        return val
    except (ValueError, TypeError):
        raise RequiredValueException(value_name, context)


def require_pos_int(
    value,
    value_name: str | None = None,
    context: str | None = None,
    not_empty: bool = True,
) -> int:
    try:
        val = parse_pos_int(value)
        if val is None and not_empty:
            raise RequiredValueException(value_name, context)
        return val
    except (ValueError, TypeError):
        raise RequiredValueException(value_name, context)


def require_ints(
    value,
    value_name: str | None = None,
    context: str | None = None,
    not_empty: bool = True,
) -> list[int]:
    if value is None:
        val = []
    elif isinstance(value, str):
        val = []
        for v in value.split(","):
            txt = v.strip()
            if txt != "":
                val.append(txt)
    else:
        value = list(value)
    int_list = []
    for i, v in enumerate(val):
        try:
            num = to_int(v, value_name, context, False)
            if num is not None:
                int_list.append(num)
        except (ValueError, TypeError):
            raise RequiredValueException(value_name, context)
    if not_empty and len(int_list) == 0:
        raise RequiredValueException(value_name, context)
    return int_list


def require_pos_ints(
    value,
    value_name: str | None = None,
    context: str | None = None,
    not_empty: bool = True,
) -> list[int]:
    int_list = require_ints(value, value_name, context, not_empty)
    for i in int_list:
        if i <= 0:
            raise RequiredValueException(value_name, context)
    return int_list


def require_in_list(
    value, values: list, value_name: str | None = None, context: str | None = None
) -> any:
    require_int(value, value_name, context)
    if value in values:
        return value
    raise RequiredValueException(value_name, context)


def require_key(value, context: str | None = None) -> str | None:
    if value is None:
        return None
    val = str(value).strip()
    if val == "":
        return None
    if Keys.is_valid(val):
        return val
    else:
        raise RequiredValueException("RealTeamMemberKey", context)


def require_keys(value, context: str | None = None) -> Keys:
    try:
        return Keys(value)
    except (ValueError, TypeError):
        raise RequiredValueException("RealTeamMemberKey", context)


def require_key_groups(
    value, context: str | None = None, allow_dups: bool | None = False
) -> KeyGroups:
    try:
        keys = KeyGroups.create(value, allow_dups=allow_dups)
        if keys is None:
            raise ValueError
        return keys
    except (ValueError, TypeError):
        raise RequiredValueException("RealTeamMemberKey", context)


def require_record(db: Session, model: type[_T], record_id: int | None) -> _T:
    record = db.get(model, record_id) if record_id else None
    if record is None:
        raise NotFoundException(object_name=model.__name__, object_id=record_id)
    return record


def require_team(db: Session, team_id: int | None) -> Team:
    return require_record(db, Team, team_id)


def require_division(db: Session, division_id: int | None) -> Division:
    return require_record(db, Division, division_id)


def require_league(db: Session, league_id: int | None) -> League:
    return require_record(db, League, league_id)


def require_transfer(db: Session, transfer_id: int | None) -> TeamMemberTransfers:
    transfer = require_record(db, TeamMemberTransfers, transfer_id)
    if transfer.transferStatus != TeamMemberTransfersStatusConstants.REQUESTED:
        raise NotFoundException(
            object_name=TeamMemberTransfers.__name__, object_id=transfer_id
        )
    return transfer


def require_team_owner(db: Session, user_id: int, team_id: int | None) -> Team:
    row = require_team(db, team_id)
    if user_owns_team(db, user_id, team=row):
        return row
    raise NotYourTeamException()


def require_division_member(
    db: Session,
    user_id: int,
    *,
    division_id: int | None = None,
    division: Division | RowMapping | dict | None = None,
    team_id: int | None = None,
    team: Team | RowMapping | dict | None = None,
) -> None:
    if not user_in_division(
        db,
        user_id,
        division_id=division_id,
        division=division,
        team_id=team_id,
        team=team,
    ):
        raise NotAMemberException(object_name="Division")


def require_league_member(
    db: Session,
    user_id: int,
    *,
    league_id: int | None = None,
    league: League | RowMapping | dict | None = None,
    division_id: int | None = None,
    division: Division | RowMapping | dict | None = None,
    team_id: int | None = None,
    team: Team | RowMapping | dict | None = None,
) -> None:
    if not user_in_league(
        db,
        user_id,
        league_id=league_id,
        league=league,
        division_id=division_id,
        division=division,
        team_id=team_id,
        team=team,
    ):
        raise NotAMemberException(object_name="League")


def require_commissioner(
    db: Session,
    user_id: int,
    *,
    league_id: int | None = None,
    league: League | RowMapping | dict | None = None,
    division_id: int | None = None,
    division: Division | RowMapping | dict | None = None,
    team_id: int | None = None,
    team: Team | RowMapping | dict | None = None,
) -> None:
    if not user_is_commissioner(
        db,
        user_id,
        league_id=league_id,
        league=league,
        division_id=division_id,
        division=division,
        team_id=team_id,
        team=team,
    ):
        raise NotACommissionerException(object_name="in the League")


def require_division_commissioner(
    db: Session,
    user_id: int,
    *,
    division_id: int | None = None,
    division: Division | RowMapping | dict | None = None,
    team_id: int | None = None,
    team: Team | RowMapping | dict | None = None,
) -> None:
    if not user_is_division_commissioner(
        db,
        user_id,
        division_id=division_id,
        division=division,
        team_id=team_id,
        team=team,
    ):
        raise NotACommissionerException(object_name="Division")


def require_league_commissioner(
    db: Session,
    user_id: int,
    *,
    league_id: int | None = None,
    league: League | RowMapping | dict | None = None,
    division_id: int | None = None,
    division: Division | RowMapping | dict | None = None,
    team_id: int | None = None,
    team: Team | RowMapping | dict | None = None,
) -> None:
    if not user_is_league_commissioner(
        db,
        user_id,
        league_id=league_id,
        league=league,
        division_id=division_id,
        division=division,
        team_id=team_id,
        team=team,
    ):
        raise NotACommissionerException(object_name="League")


def _get_value(obj: SQLModel | RowMapping | dict | None, name: str) -> Any:
    if isinstance(obj, SQLModel):
        return getattr(obj, name)
    return obj[name] if obj is not None else None
