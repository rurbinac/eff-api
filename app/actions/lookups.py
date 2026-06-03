from datetime import datetime
from sqlalchemy.orm import Session
from app.models import Lookup
from app.context import RequestContext


class LookupsReadListAction:
    """Handle Lookups ReadList requests."""

    @staticmethod
    def execute(db: Session, lookup_num: int | None = None) -> dict:
        """
        Get lookups filtered by lookup number.

        Args:
            db: Database session
            lookup_num: Filter by lookupNum (optional, returns all if None)

        Returns:
            PHP-compatible response dict
        """
        query = db.query(Lookup)

        if lookup_num is not None:
            query = query.filter(Lookup.lookupNum == lookup_num)

        lookups = query.all()

        items = []
        for lookup in lookups:
            items.append({
                "values": {
                    "lookupID": lookup.lookupID,
                    "lookupNum": lookup.lookupNum,
                    "position": lookup.position,
                    "lookupKey": lookup.lookupKey,
                    "lookupCode": lookup.lookupCode,
                    "lookupText": lookup.lookupText,
                }
            })

        return {
            "table": "Lookups",
            "timestamp": RequestContext.get_datetime().strftime("%Y-%m-%d %H:%M:%S"),
            "items": items,
        }
