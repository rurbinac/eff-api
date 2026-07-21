from datetime import datetime, timedelta

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.context import RequestContext
from app.services.query import QueryService

ADD_DAYS = 2


def div_map_days_map_key(
    db: Session, divCnt: int, rcID: int | None = None, dt: datetime | None = None
) -> str | None:
    if rcID is None:
        rcID = _get_rcID(db)
    if rcID is not None:
        if dt is None:
            dt = RequestContext.get_datetime()
        if divCnt == 8 or divCnt == 10:
            return _find(db, dt, f"{rcID:02},__,{divCnt:02}")
    return None


def lea_map_days_map_key(
    db: Session, leaCnt: int, key: str | None = None, dt: datetime | None = None
) -> str | None:
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


def split_map_days_map_key(key: str | None) -> tuple[int]:
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


def split_map_days_map_key_div(key: str | None) -> tuple[int]:
    values = split_map_days_map_key(key)
    return values[:3]


def split_map_days_map_key_lea(key: str | None) -> tuple[int]:
    values = split_map_days_map_key(key)
    return values[:1] + values[-2:]


def _get_rcID(db: Session) -> int | None:
    baseRC = QueryService.get_current_base_competition(db)
    return None if baseRC is None else baseRC["baseRealCompetitionID"]


def _find(db: Session, dt: datetime, key: str) -> str | None:
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
