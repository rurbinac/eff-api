def to_int(val, default: int | None = None) -> int | None:
    if isinstance(val, int):
        return val
    if val is None:
        return default
    try:
        txt = str(val).strip()
        if txt != "":
            return int(txt)
    except (ValueError, TypeError):
        pass
    return default

def to_float(val, default: float | None = None) -> float | None:
    if isinstance(val, float):
        return val
    if val is None:
        return default
    try:
        txt = str(val).strip()
        if txt != "":
            return float(txt)
    except (ValueError, TypeError):
        pass
    return default

def if_none(val, default = None):
    return default if val is None else val
