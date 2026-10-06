def parse_int(value, default: int | None = None) -> int | None:
    if isinstance(value, int):
        return value
    if value is None:
        return default
    txt = str(value).strip()
    if txt == "":
        return default
    return int(txt)


def parse_pos_int(value, default: int | None = None) -> int | None:
    i = parse_int(value, default=default)
    if i <= 0:
        raise ValueError
    return i


def parse_ints(value) -> list[int]:
    if value is None:
        return []
    if isinstance(value, int):
        return [value]
    if isinstance(value, list):
        values = []
        for v in value:
            i = parse_int(v)
            if i is None:
                continue
            values.append(v)
        return values
    return parse_ints(str(value).split(i))


def parse_pos_ints(value) -> list[int]:
    values = parse_ints(value)
    for i in values:
        if i <= 0:
            raise ValueError
    return values


def parse_float(value, default: float | None = None) -> float | None:
    if isinstance(value, float):
        return value
    if value is None:
        return default
    txt = str(value).strip()
    if txt == "":
        return default
    return float(txt)


def parse_pos_float(value, default: float | None = None) -> float | None:
    i = parse_float(value, default=default)
    if i <= 0:
        raise ValueError
    return i


def parse_floats(value) -> list[float]:
    if value is None:
        return []
    if isinstance(value, float):
        return [value]
    if isinstance(value, list):
        values = []
        for v in value:
            i = parse_float(v)
            if i is None:
                continue
            values.append(v)
        return values
    return parse_floats(str(value).split(i))


def parse_pos_floats(value) -> list[float]:
    values = parse_floats(value)
    for i in values:
        if i <= 0:
            raise ValueError
    return values


def to_int(value, default: int | None = None) -> int | None:
    try:
        return parse_int(value, default=default)
    except (ValueError, TypeError):
        return default


def to_pos_int(value, default: int | None = None) -> int | None:
    try:
        return parse_pos_int(value, default=default)
    except (ValueError, TypeError):
        return default


def to_ints(value, default: list[int] | None = None) -> list[int] | None:
    try:
        return parse_ints(value, default=default)
    except (ValueError, TypeError):
        return default


def to_pos_ints(value, default: list[int] | None = None) -> list[int] | None:
    try:
        return parse_pos_ints(value, default=default)
    except (ValueError, TypeError):
        return default


def to_float(value, default: float | None = None) -> float | None:
    try:
        return parse_float(value, default=default)
    except (ValueError, TypeError):
        return default


def to_floats(value, default: list[float] | None = None) -> list[float] | None:
    try:
        return parse_floats(value, default=default)
    except (ValueError, TypeError):
        return default


def to_pos_floats(value, default: list[float] | None = None) -> list[float] | None:
    try:
        return parse_pos_floats(value, default=default)
    except (ValueError, TypeError):
        return default


def if_none(val, default=None):
    return default if val is None else val
