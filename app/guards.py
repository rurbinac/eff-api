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
    user_id: int,
    *,
    team_id: int | None = None,
    team: Team | RowMapping | dict | None = None,
) -> bool:
    """True if the user is the owner of the given team."""
    if team is not None:
        return (team["userID"] if isinstance(team, dict) else team.userID) == user_id
    if team_id is None:
        return False
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
    if division is not None:
        division_id = division["divisionID"] if isinstance(division, dict) else division.divisionID
    if team is not None:
        if division_id is not None and division_id != (team["divisionID"] if isinstance(team, dict) else team.divisionID):
            return False
        return user_owns_team(db, user_id, team=team)
    if team_id is not None:
        if division_id is not None:
            return (
                db.query(Team)
                .filter(Team.teamID == team_id, Team.divisionID == division_id, Team.userID == user_id)
                .first()
            ) is not None
        return user_owns_team(db, user_id, team_id=team_id)
    if division_id is None:
        raise ValueError("user_in_division requires division_id, or team_id")
    return (
        db.query(Team)
        .filter(Team.divisionID == division_id, Team.userID == user_id)
        .first()
    ) is not None


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
    if league is not None:
        league_id = league["leagueID"] if isinstance(league, dict) else league.leagueID
    if team is not None:
        if league_id is not None and league_id != (team["leagueID"] if isinstance(team, dict) else team.leagueID):
            return False
        return user_owns_team(db, user_id, team=team)
    if division is not None:
        if league_id is not None and league_id != (division["leagueID"] if isinstance(division, dict) else division.leagueID):
            return False
        division_id = division["divisionID"] if isinstance(division, dict) else division.divisionID
    if team_id is not None or division_id is not None:
        return user_in_division(db, user_id, division_id=division_id, team_id=team_id)
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
    if team is not None:
        t = team
        commissioner_id = t["commissionerID"] if isinstance(t, dict) else t.commissionerID
        is_commissioner = t["isCommissioner"] if isinstance(t, dict) else t.isCommissioner
        team_user_id = t["userID"] if isinstance(t, dict) else t.userID
        team_division_id = t["divisionID"] if isinstance(t, dict) else t.divisionID
        if commissioner_id == user_id or (is_commissioner and team_user_id == user_id):
            return True
        return user_is_division_commissioner(db, user_id, division_id=team_division_id)
    if team_id is not None:
        row = (
            db.query(Team)
            .filter(Team.teamID == team_id, Team.userID == user_id)
            .first()
        )
        return (
            False
            if row is None
            else row.isCommissioner or row.commissionerID == user_id
        )
    if division is not None:
        division_id = division["divisionID"] if isinstance(division, dict) else division.divisionID
    if division_id is not None:
        row = (
            db.query(Team)
            .filter(Team.divisionID == division_id, Team.userID == user_id)
            .first()
        )
        return (
            False
            if row is None
            else row.isCommissioner or row.commissionerID == user_id
        )

    raise ValueError(
        "user_is_division_commissioner requires division_id, team_id, or league_id"
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
    if team is not None:
        return (team["commissionerID"] if isinstance(team, dict) else team.commissionerID) == user_id
    if team_id is not None:
        return (
            db.query(Team)
            .filter(Team.teamID == team_id, Team.commissionerID == user_id)
            .first()
        ) is not None
    if division is not None:
        return (division["commissionerID"] if isinstance(division, dict) else division.commissionerID) == user_id
    if division_id is not None:
        return (
            db.query(Division)
            .filter(
                Division.divisionID == division_id, Division.commissionerID == user_id
            )
            .first()
        ) is not None
    if league is not None:
        return (league["commissionerID"] if isinstance(league, dict) else league.commissionerID) == user_id
    if league_id is not None:
        return (
            db.query(League)
            .filter(League.leagueID == league_id, League.commissionerID == user_id)
            .first()
        ) is not None
    raise ValueError(
        "user_is_league_commissioner requires league_id, division_id or team_id"
    )


# ---------------------------------------------------------------------------
# Raising variants — accept int | None so callers skip the None check
# ---------------------------------------------------------------------------


def require_team(db: Session, team_id: int | None) -> Team:
    row = db.query(Team).filter(Team.teamID == team_id).first() if team_id else None
    if row:
        return row
    raise NotFoundException(object_name="Team", object_id=team_id)


def require_division(db: Session, division_id: int | None) -> Division:
    row = (
        db.query(Division).filter(Division.divisionID == division_id).first()
        if division_id
        else None
    )
    if row:
        return row
    raise NotFoundException(object_name="Division", object_id=division_id)


def require_league(db: Session, league_id: int | None) -> League:
    row = (
        db.query(League).filter(League.leagueID == league_id).first()
        if league_id
        else None
    )
    if row:
        return row
    raise NotFoundException(object_name="League", object_id=league_id)


def require_team_owner(db: Session, user_id: int, team_id: int | None) -> None:
    row = require_team(db, team_id)
    if not user_owns_team(db, user_id, team=row):
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
