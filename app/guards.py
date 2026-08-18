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

from sqlalchemy import RowMapping
from sqlalchemy.orm import Session

from app.exceptions import (
    NotACommissionerException,
    NotAMemberException,
    NotFoundException,
    NotYourTeamException,
)
from app.models import Division, League, Team

# ---------------------------------------------------------------------------
# Bool checks
# ---------------------------------------------------------------------------


def user_owns_team(
    db: Session,
    user_id: int | None,
    team_id: int | None,
    team: RowMapping | None = None,
) -> bool:
    """True if the user is the owner of the given team."""
    if user_id is None:
        return False
    if isinstance(team, RowMapping):
        return team.get("userID") == user_id
    if team_id is None:
        return False
    return (
        db.query(Team).filter(Team.teamID == team_id, Team.userID == user_id).first()
    ) is not None


def user_in_division(
    db: Session,
    user_id: int,
    division_id: int | None = None,
    *,
    team_id: int | None = None,
    division: RowMapping | None = None,
    team: RowMapping | None = None,
) -> bool:
    """True if the user has a team in the given division.

    The division can be identified by ``division_id`` or ``team_id``
    (the division that team belongs to).  Raises ``ValueError`` if
    neither is provided.
    """
    if isinstance(team, RowMapping):
        division_id = team.get("divisionID")
    elif isinstance(division, RowMapping):
        division_id = division.get("divisionID")
    elif team_id is not None:
        row = db.query(Team.divisionID).filter(Team.teamID == team_id).first()
        if row is None:
            return False
        division_id = row[0]

    if division_id is None:
        raise ValueError("user_in_division requires division_id or team_id")

    return (
        db.query(Team)
        .filter(Team.divisionID == division_id, Team.userID == user_id)
        .first()
    ) is not None


def user_in_league(
    db: Session,
    user_id: int,
    league_id: int | None = None,
    *,
    division_id: int | None = None,
    team_id: int | None = None,
) -> bool:
    """True if the user has a team in the given league.

    The league can be identified by ``league_id``, ``division_id``, or
    ``team_id`` — first non-None wins.  Raises ``ValueError`` if none
    of the three is provided.
    """
    if team_id is not None:
        row = db.query(Team.leagueID).filter(Team.teamID == team_id).first()
        if row is None:
            return False
        league_id = row[0]
    elif division_id is not None:
        row = (
            db.query(Division.leagueID)
            .filter(Division.divisionID == division_id)
            .first()
        )
        if row is None:
            return False
        league_id = row[0]

    if league_id is None:
        raise ValueError("user_in_league requires league_id, division_id, or team_id")

    return (
        db.query(Team)
        .filter(Team.leagueID == league_id, Team.userID == user_id)
        .first()
    ) is not None


def user_is_division_commissioner(
    db: Session,
    user_id: int,
    division_id: int | None = None,
    *,
    league_id: int | None = None,
    team_id: int | None = None,
) -> bool:
    """True if the user is a division commissioner.

    Three ways to identify the scope — first non-None wins:

    * ``division_id`` — commissioner of that specific division.
    * ``team_id``     — commissioner of the division that team belongs to.
    * ``league_id``   — commissioner of *any* division in that league.

    Raises ``ValueError`` if none of the three is provided.

    Checked via the Teams table (``isCommissioner == 1``).
    ``Division.commissionerID`` is a denormalised copy from Leagues and
    should not be used for this check.
    """
    if team_id is not None:
        row = db.query(Team.divisionID).filter(Team.teamID == team_id).first()
        if row is None:
            return False
        division_id = row[0]

    if division_id is not None:
        return (
            db.query(Team)
            .filter(
                Team.divisionID == division_id,
                Team.userID == user_id,
                Team.isCommissioner == 1,
            )
            .first()
        ) is not None

    if league_id is not None:
        return (
            db.query(Team)
            .filter(
                Team.leagueID == league_id,
                Team.userID == user_id,
                Team.isCommissioner == 1,
            )
            .first()
        ) is not None

    raise ValueError(
        "user_is_division_commissioner requires division_id, team_id, or league_id"
    )


def user_is_league_commissioner(
    db: Session,
    user_id: int,
    league_id: int | None = None,
    *,
    division_id: int | None = None,
    team_id: int | None = None,
) -> bool:
    """True if the user is the commissioner of the given league.

    The league can be identified by ``league_id``, ``division_id``, or
    ``team_id`` — first non-None wins.  Raises ``ValueError`` if none
    of the three is provided.
    """
    if team_id is not None:
        row = db.query(Team.leagueID).filter(Team.teamID == team_id).first()
        if row is None:
            return False
        league_id = row[0]
    elif division_id is not None:
        row = (
            db.query(Division.leagueID)
            .filter(Division.divisionID == division_id)
            .first()
        )
        if row is None:
            return False
        league_id = row[0]

    if league_id is None:
        raise ValueError(
            "user_is_league_commissioner requires league_id, division_id, or team_id"
        )

    return (
        db.query(League)
        .filter(League.leagueID == league_id, League.commissionerID == user_id)
        .first()
    ) is not None


def user_is_commissioner(
    db: Session,
    user_id: int,
    league_id: int | None = None,
    *,
    division_id: int | None = None,
    team_id: int | None = None,
) -> bool:
    """True if the user is the league commissioner OR a division commissioner.

    Accepts the same ``league_id`` / ``division_id`` / ``team_id`` options as
    :func:`user_is_league_commissioner` and :func:`user_is_division_commissioner`.
    Raises ``ValueError`` if none of the three is provided.

    Identifiers are resolved once here so the two sub-checks each do at most
    one query.
    """
    if team_id is not None:
        row = (
            db.query(Team.leagueID, Team.divisionID)
            .filter(Team.teamID == team_id)
            .first()
        )
        if row is None:
            return False
        league_id, division_id = row[0], row[1]
    elif division_id is not None and league_id is None:
        row = (
            db.query(Division.leagueID)
            .filter(Division.divisionID == division_id)
            .first()
        )
        if row is None:
            return False
        league_id = row[0]

    if league_id is None and division_id is None:
        raise ValueError(
            "user_is_commissioner requires league_id, division_id, or team_id"
        )

    return user_is_league_commissioner(
        db, user_id, league_id
    ) or user_is_division_commissioner(db, user_id, division_id, league_id=league_id)


# ---------------------------------------------------------------------------
# Raising variants — accept int | None so callers skip the None check
# ---------------------------------------------------------------------------


def require_team(
    db: Session, user_id: int | None, team: RowMapping | None = None
) -> None:
    """Raise 404 if the team doesn't exist, 403 if the user doesn't own it."""
    if not team:
        raise NotFoundException(object_name="Team")
    require_team_owner(db, user_id, team=team)


def require_team_owner(
    db: Session,
    user_id: int | None,
    team_id: int | None = None,
    team: RowMapping | None = None,
) -> None:
    """Raise HTTP 403 if the user does not own the team."""
    if not user_owns_team(db, user_id, team_id=team_id, team=team):
        raise NotYourTeamException()


def require_division_member(
    db: Session,
    user_id: int | None,
    division_id: int | None = None,
    *,
    team_id: int | None = None,
    division: RowMapping | None = None,
    team: RowMapping | None = None,
) -> None:
    """Raise HTTP 403 if the user has no team in the division.

    Accepts the same ``division_id`` / ``team_id`` options as
    :func:`user_in_division`.
    """
    if user_id is None or not user_in_division(
        db, user_id, division_id, team_id=team_id, team=team, division=division
    ):
        raise NotAMemberException(object_name="division")


def require_league_member(
    db: Session,
    user_id: int | None,
    league_id: int | None = None,
    *,
    division_id: int | None = None,
    team_id: int | None = None,
) -> None:
    """Raise HTTP 403 if the user has no team in the league.

    Accepts the same ``league_id`` / ``division_id`` / ``team_id`` options
    as :func:`user_in_league`.
    """
    if user_id is None or not user_in_league(
        db, user_id, league_id, division_id=division_id, team_id=team_id
    ):
        raise NotAMemberException(object_name="league")


def require_division_commissioner(
    db: Session,
    user_id: int | None,
    division_id: int | None = None,
    *,
    league_id: int | None = None,
    team_id: int | None = None,
) -> None:
    """Raise HTTP 403 if the user is not a division commissioner.

    Accepts the same ``division_id`` / ``team_id`` / ``league_id`` options as
    :func:`user_is_division_commissioner`.
    """
    if user_id is None or not user_is_division_commissioner(
        db, user_id, division_id, league_id=league_id, team_id=team_id
    ):
        raise NotACommissionerException(object_name="division")


def require_league_commissioner(
    db: Session,
    user_id: int | None,
    league_id: int | None = None,
    *,
    division_id: int | None = None,
    team_id: int | None = None,
) -> None:
    """Raise HTTP 403 if the user is not the league commissioner.

    Accepts the same ``league_id`` / ``division_id`` / ``team_id`` options as
    :func:`user_is_league_commissioner`.
    """
    if user_id is None or not user_is_league_commissioner(
        db, user_id, league_id, division_id=division_id, team_id=team_id
    ):
        raise NotACommissionerException(object_name="league")


def require_commissioner(
    db: Session,
    user_id: int | None,
    league_id: int | None = None,
    *,
    division_id: int | None = None,
    team_id: int | None = None,
) -> None:
    """Raise HTTP 403 if the user is neither league nor division commissioner.

    Accepts the same ``league_id`` / ``division_id`` / ``team_id`` options as
    :func:`user_is_commissioner`.
    """
    if user_id is None or not user_is_commissioner(
        db, user_id, league_id, division_id=division_id, team_id=team_id
    ):
        raise NotACommissionerException(object_name=None)
