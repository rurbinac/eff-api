from typing import Any
from sqlalchemy.orm import Session
from sqlalchemy import update as sa_update
from sqlmodel import SQLModel


def optimistic_update(
    db: Session,
    model: type[SQLModel],
    pk: dict[str, Any],
    new_values: dict[str, Any],
    old_values: dict[str, Any],
) -> bool:
    """
    Update a row only if the old_values still match the current database state.
    Returns True if the row was updated, False if a conflict was detected.

    pk:         primary key field(s), e.g. {"divisionID": 130}
    new_values: fields to SET
    old_values: fields to check in WHERE — only include fields relevant to the
                operation so unrelated changes (e.g. comments) don't cause conflicts
    """
    stmt = sa_update(model)

    for field, value in pk.items():
        stmt = stmt.where(getattr(model, field) == value)

    for field, value in old_values.items():
        stmt = stmt.where(getattr(model, field) == value)

    stmt = stmt.values(**new_values)

    result = db.execute(stmt)
    return result.rowcount == 1
