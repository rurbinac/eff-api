from app.context import RequestContext
from app.exceptions import EFFException


def return_one_legacy(table: str, value: dict) -> dict:
    return {
        "success": True,
        "timestamp": RequestContext.get_datetime_iso(),
        "table": table,
        "values": value,
    }


def return_many_legacy(table: str, values: list[dict]) -> dict:
    return {
        "success": True,
        "timestamp": RequestContext.get_datetime_iso(),
        "table": table,
        "items": [{"values": item} for item in values],
    }

def return_error(ex: EFFException, table: str | None = None) -> dict:
    data = {"success": False,
            "timestamp": RequestContext.get_datetime_iso()}
    if table:
        data["table"] = table
    data["message"] = str(ex)
    return data
