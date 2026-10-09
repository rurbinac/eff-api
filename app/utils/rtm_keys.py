from __future__ import annotations

from collections import UserList
from collections.abc import Callable
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from app.utils.readers import KeysReader

from app.constants import DraftPositionConstants
from app.utils.scalars import parse_pos_ints, to_pos_int


class Keys(UserList):
    """Validated list of member keys (e.g. 'P123', 'T7').

    Behaves like a regular list but rejects any item that is not a valid
    member key (must start with 'P' or 'T' followed by a positive integer).
    Duplicate handling is controlled by the allow_dups constructor parameter —
    the same three-mode semantics as MKeys (False=error, None=skip, True=allow).
    Also provides static helpers for parsing, building, and serialising keys.
    """

    PLAYER: ClassVar[str] = "P"
    TEAM: ClassVar[str] = "T"
    SUFFIX: ClassVar[str] = "."
    _SUFFIX: ClassVar[str] = ","

    @staticmethod
    def is_valid(key: str) -> bool:
        """Return True if key is a valid member key ('P' or 'T' followed by a positive integer)."""
        return Keys.split(key)[0] is not None

    @staticmethod
    def is_player(key: str) -> bool:
        """Return True if key is a valid player key (starts with 'P')."""
        return Keys.split(key)[0] == Keys.PLAYER

    @staticmethod
    def is_team(key: str) -> bool:
        """Return True if key is a valid team key (starts with 'T')."""
        return Keys.split(key)[0] == Keys.TEAM

    @staticmethod
    def split(key: str) -> tuple[str | None, int | None]:
        """Split a key into its prefix ('P'/'T') and numeric id.

        Returns (prefix, id) on success, (None, None) if the key is invalid.
        """
        k = key.strip(" " + Keys.SUFFIX + Keys._SUFFIX)
        if len(k) > 1 and k.startswith((Keys.PLAYER, Keys.TEAM)):
            num = to_pos_int(k[1:])
            if num is not None:
                return (k[0:1], num)
        return (None, None)

    @staticmethod
    def build_keys(suffix: str, id: int) -> str | None:
        """Build a single key string from a prefix ('P'/'T') and a positive integer id.

        Returns None if suffix is not 'P'/'T' or id is not positive.
        """
        return (
            suffix + str(id) if suffix in (Keys.PLAYER, Keys.TEAM) and id > 0 else None
        )

    @staticmethod
    def build_player_keys(
        ids: int | str | list | None, default: list[str] | None = None
    ) -> list[str] | None:
        """Build one or more player key strings from an id or list of ids.

        Returns a single string for a scalar id, a list for a list of ids,
        or None if any id is invalid.
        """
        return Keys._build_member_keys(ids, Keys.PLAYER, default)

    @staticmethod
    def build_team_keys(
        ids: int | str | list | None, default: list[str] | None = None
    ) -> list[str] | None:
        """Build one or more team key strings from an id or list of ids.

        Returns a single string for a scalar id, a list for a list of ids,
        or None if any id is invalid.
        """
        return Keys._build_member_keys(ids, Keys.TEAM, default)

    @staticmethod
    def to_str(value: str | list[str] | Keys | None) -> str | None:
        """Serialise keys to a packed dot-separated string (e.g. 'P1.P2.T3.').

        Accepts a Keys instance, a list of key strings, a single key string,
        or None. Returns an empty string for None or an empty collection,
        and None if any key is invalid.
        """
        if isinstance(value, Keys):
            return value.pack()
        as_list = Keys.to_list(value)
        return None if as_list is None else _keys_list_to_str(as_list)

    @staticmethod
    def to_list(value: str | list[str] | Keys | None) -> list[str] | None:
        """Parse keys into a flat list of key strings.

        Accepts any key string format: dot-separated ('P1.P2.T3.'), comma-separated,
        space-separated, concatenated ('P1P2T3'), or mixed — as well as a list of key
        strings, a Keys instance, or None. Returns an empty list for None or empty
        input, and None if any key is invalid. Always returns a copy.
        """
        if value is None:
            return []
        elif isinstance(value, Keys):
            return value.data.copy()
        elif isinstance(value, list):
            return value.copy() if all(map(Keys.is_valid, value)) else None
        elif isinstance(value, str):
            as_list = _keys_str_to_list(value)
            return as_list if all(map(Keys.is_valid, as_list)) else None
        return None

    @staticmethod
    def create(
        value: str | list[str] | Keys | None, allow_dups: bool | None = False
    ) -> Keys | None:
        if value is None:
            as_list = []
        else:
            as_list = Keys.to_list(value)
            if as_list is None:
                return None
        try:
            return Keys(as_list, allow_dups=allow_dups)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _build_member_keys(
        ids: int | str | list, suffix: str, default: list[str] | None
    ) -> list[str] | None:
        """Build key string(s) from one or more ids using the given prefix."""
        try:
            return [str(i) + suffix for i in parse_pos_ints(ids)]
        except (ValueError, TypeError):
            return default

    def __init__(self, initlist=None, allow_dups: bool | None = False):
        """Create a validated list of member keys.

        Args:
            initlist: Optional initial keys (list or iterable).
            allow_dups: Duplicate-key policy (checked globally across the list):
                False — duplicate raises ValueError (default).
                None  — duplicate is silently skipped; first occurrence kept.
                True  — duplicates are allowed.
        """
        self._allow_dups = allow_dups
        self.data = []
        if initlist is not None:
            # Route through extend so validation and dup-checking apply.
            raw, initlist = initlist, Keys.to_list(initlist)
            if initlist is None:
                raise ValueError(f"Invalid member keys: {raw!r}")
            elif len(initlist) > 0:
                self.extend(initlist)

    @property
    def allow_dups(self) -> bool | None:
        """Duplicate-key policy: True=allowed, False=error, None=silently skipped."""
        return self._allow_dups

    def unpack(self, data: str | list[str] | None) -> bool:
        """Replace the current keys with those parsed from data.

        Args:
            data: A packed string (e.g. 'P1.P2.T3.'), a list of key strings,
                or None to clear the list.

        Returns:
            True on success, False if data contains invalid keys or violates
            the duplicate policy.
        """
        if data is not None:
            data = Keys.to_list(data)
            if data is None:
                return False
        self.data = data
        return True

    def pack(self) -> str:
        """Serialise the current keys to a packed string (e.g. 'P1.P2.T3.').

        Returns an empty string if the list is empty.
        """
        return _keys_list_to_str(self.data)

    def check(self) -> None:
        """Re-validate all keys and enforce the duplicate policy.

        Raises ValueError if any key is invalid or if the current allow_dups
        policy is violated. Useful after direct mutation of self.data.
        """
        Keys(self.data, allow_dups=self._allow_dups)

    def append(self, item) -> None:
        self._validate(item)
        if not self._check_dup(item):
            self.data.append(item)

    def insert(self, i, item) -> None:
        self._validate(item)
        if not self._check_dup(item):
            self.data.insert(i, item)

    def extend(self, other) -> None:
        self.data.extend(self._validate_all(other))

    def __str__(self) -> str:
        return self.pack()

    def __setitem__(self, i, item) -> None:
        if isinstance(i, slice):
            self.data[i] = self._validate_all(item)
        else:
            self._validate(item)
            if not self._check_dup(item):
                self.data[i] = item

    def __iadd__(self, other):
        self.extend(other)
        return self

    def __add__(self, other):
        result = self.__class__(allow_dups=self._allow_dups)
        result.data = self.data.copy()
        result.extend(other)
        return result

    def _validate(self, item) -> None:
        """Raise ValueError if item is not a valid member key."""
        if not Keys.is_valid(item):
            raise ValueError(f"Invalid member key: {item!r}")

    def _check_dup(self, item) -> bool:
        """Check whether item is a duplicate of an existing key.

        Returns True if the item should be skipped (allow_dups is None).
        Raises ValueError if duplicates are not allowed (allow_dups is False).
        Returns False if the item is not a duplicate or duplicates are allowed.
        """
        if self._allow_dups is True or item not in self.data:
            return False
        if self._allow_dups is False:
            raise ValueError(f"Duplicate key: {item!r}")
        return True  # allow_dups is None → skip silently

    def _validate_all(self, iterable) -> list:
        """Validate all items and apply duplicate policy, returning the filtered list."""
        items = list(iterable)
        for item in items:
            self._validate(item)
        if self._allow_dups is True:
            return items
        seen: set[str] = set(self.data)
        result = []
        for item in items:
            if item in seen:
                if self._allow_dups is False:
                    raise ValueError(f"Duplicate key: {item!r}")
                # allow_dups is None → skip
            else:
                seen.add(item)
                result.append(item)
        return result


class GroupedKeys(Keys):
    """Keys slot inside KeyGroups; dup behaviour is governed by the parent's allow_dups.

    Within-slot duplicates are always silently skipped (allow_dups=False on self).
    Cross-group duplicates: raise ValueError (False), skip silently (None), or allow (True).
    """

    def __init__(self, parent: KeyGroups, group: int):
        self._parent = parent
        self._group = group
        super().__init__(allow_dups=False)

    @property
    def parent(self) -> KeyGroups:
        return self._parent

    @property
    def group(self) -> int:
        return self._group

    def append(self, item) -> None:
        self._validate(item)
        self._parent._add(self._group, item)

    def _clear(self) -> None:
        self.data = []


class KeyGroups:
    """Fixed-size sequence of Keys groups, serialised as groups joined by ':'.

    e.g. size=4, packed: 'P1.P2.:T3.::P4.'
    Cross-group duplicates are always rejected (raises ValueError in GroupedKeys).
    """

    DELIM: ClassVar[str] = ":"
    _DELIM: ClassVar[str] = ";"

    def __init__(self, size: int, allow_dups: bool | None = False):
        self._allow_dups = allow_dups
        self._keys: list[GroupedKeys] = [GroupedKeys(self, i) for i in range(size)]

    # --- static helpers (used by callers that don't need a sized instance) ---

    @staticmethod
    def to_str(value: str | list | Keys | KeyGroups | None) -> str | None:
        if isinstance(value, (Keys, KeyGroups)):
            return value.pack()
        as_list = KeyGroups.to_list(value)
        if as_list is None:
            return None
        return KeyGroups.DELIM.join(_keys_list_to_str(keys) for keys in as_list)

    @staticmethod
    def to_list(value: str | list | Keys | KeyGroups | None) -> list[list[str]] | None:
        """Parse packed string or list into a list of key lists.

        Returns empty list for None/empty input, None if any key is invalid.
        """
        if value is None:
            return []
        if isinstance(value, KeyGroups):
            return [list(k) for k in value._keys]
        if isinstance(value, Keys):
            return [list(value.data)]
        if isinstance(value, str):
            if not value.strip():
                return []
            result = []
            for part in (
                value.replace(KeyGroups._DELIM, KeyGroups.DELIM)
                .replace(" ", "")
                .split(KeyGroups.DELIM)
            ):
                keys = Keys.to_list(part) if part else []
                if keys is None:
                    return None
                result.append(keys)
            return result
        if isinstance(value, list):
            result = []
            for g in value:
                keys = Keys.to_list(g if isinstance(g, (str, list, Keys)) else None)
                if keys is None:
                    return None
                result.append(keys)
            return result
        return None

    @staticmethod
    def create(
        value: str | list | Keys | KeyGroups | None,
        size: int | None = None,
        allow_dups: bool | None = False,
    ) -> KeyGroups | None:
        try:
            if size is not None and size <= 0:
                return None
            if value is None:
                as_list = []
            else:
                as_list = KeyGroups.to_list(value)
                if as_list is None:
                    return None
                if size is None:
                    size = len(as_list)
                elif size < len(as_list):
                    return None
            key_gr = KeyGroups(size=size, allow_dups=allow_dups)
            if len(as_list) > 0 and not key_gr.unpack(as_list):
                return None
            return key_gr
        except (ValueError, TypeError):
            return None

    # --- instance methods ---

    @property
    def allow_dups(self) -> bool | None:
        return self._allow_dups

    def compress(self) -> None:
        non_empty = [g for g in self._keys if len(g) > 0]
        for i, g in enumerate(non_empty):
            g._group = i
        self._keys = non_empty

    def find(self, key: str) -> list[int]:
        """Return the list of group indices containing key (empty if not found)."""
        found = []
        for i, keys in enumerate(self._keys):
            if key in keys:
                found.append(i)
        return found

    def reset(self) -> None:
        for k in self._keys:
            k._clear()

    def pack(self) -> str:
        """Serialise to a packed string (e.g. 'P1.P2.:T3.::P4.')."""
        return self.DELIM.join(k.pack() for k in self._keys)

    def unpack(self, data: str | list | KeyGroups | None) -> bool:
        """Replace group contents from a packed string, list, or KeyGroups.

        Fills slots left-to-right; extra groups beyond size cause a False return.
        Returns True on success, False on invalid data or duplicate key across groups.
        """
        self.reset()
        if data is None:
            return True
        as_list = KeyGroups.to_list(data)
        if as_list is None or len(as_list) > len(self._keys):
            return False
        try:
            for i, group in enumerate(as_list):
                for key in group:
                    self._keys[i].append(key)
        except ValueError:
            self.reset()
            return False
        return True

    def count(self, unique: bool = False) -> int:
        if unique and self._allow_dups is True:
            return len({key for k in self._keys for key in k})
        return sum(len(k) for k in self._keys)

    def can_add(self, group: int, key: str) -> bool:
        """Return True if key can be added to group without violating any constraint."""
        if not Keys.is_valid(key):
            return False
        can, _ = self._fake_add(group, key)
        return can

    def has_key(self, key: str, group: int | None = None) -> bool:
        """Return True if key exists in the specified group, or any group if group is None."""
        if group is None:
            return len(self.find(key)) > 0
        if group < 0 or group >= len(self._keys):
            return False
        return key in self._keys[group]

    def remove_key(self, key: str, group: int | None = None) -> bool:
        """Remove key from the specified group, or from whichever group contains it.

        Returns True if removed, False if not found.
        """
        if group is None:
            found = self.find(key)
            if not found:
                return False
            for i in found:
                self._keys[i].data.remove(key)
            return True
        if group < 0 or group >= len(self._keys):
            return False
        if key not in self._keys[group]:
            return False
        self._keys[group].data.remove(key)
        return True

    def move_key(self, key: str, from_group: int, to_group: int) -> bool:
        """Move key from one group to another.

        Returns True on success, False if key not in from_group or to_group invalid.
        """
        if from_group < 0 or from_group >= len(self._keys):
            return False
        if to_group < 0 or to_group >= len(self._keys):
            return False
        if key not in self._keys[from_group]:
            return False
        if from_group == to_group:
            return True
        self._keys[from_group].data.remove(key)
        try:
            self._keys[to_group].append(key)
        except ValueError:
            self._keys[from_group].data.append(key)  # roll back
            return False
        return True

    def __len__(self) -> int:
        return len(self._keys)

    def __iter__(self):
        return iter(self._keys)

    def __getitem__(self, index):
        return self._keys[index]

    def _add(self, group: int, key: str) -> None:
        can, err_msg = self._fake_add(group, key)
        if can:
            self._keys[group].data.append(key)
        elif err_msg:
            raise ValueError(err_msg)

    def _fake_add(self, group: int, key: str) -> tuple[bool, str]:
        if group < 0 or group >= len(self._keys):
            return False, f"Wrong group: {group!r}"  # Should never happen
        found = self.find(key)
        if len(found) == 0 or self._allow_dups is True and group not in found:
            return True, ""
        elif self._allow_dups is False:
            return False, f"Duplicate key: {key!r}"
        return False, ""


def collect_by_dp(
    keys: Keys | KeyGroups,
    get_dp: KeysReader | Callable[[str], str | None],
    by_dp: dict[str, list[str]] | None = None,
) -> dict[str, list[str]]:
    if hasattr(get_dp, "get_dp"):
        get_dp = get_dp.get_dp
    if by_dp is None:
        by_dp: dict[str, list[str]] = {
            dp: [] for dp in DraftPositionConstants.valid_values()
        }
        by_dp[DraftPositionConstants.UNKNOWN] = []
    if isinstance(keys, Keys):
        for key in keys:
            dp = get_dp(key)
            by_dp[DraftPositionConstants.UNKNOWN if dp is None else dp].append(key)
    elif isinstance(keys, KeyGroups):
        for k in keys._keys:
            collect_by_dp(k, get_dp, by_dp)
    else:
        return {}
    return by_dp


def count_by_dp(
    keys: Keys | KeyGroups, get_dp: KeysReader | Callable[[str], str | None]
) -> dict[str, int]:
    cnt_dp: dict[str, int] = {
        DraftPositionConstants.MEMBER: 0,
        DraftPositionConstants.PLAYER: 0,
    }
    for dp, k in collect_by_dp(keys, get_dp).items():
        cnt = len(k)
        cnt_dp[dp] = cnt
        if dp != DraftPositionConstants.UNKNOWN:
            cnt_dp[DraftPositionConstants.MEMBER] += cnt
            if dp != DraftPositionConstants.EPL_TEAM:
                cnt_dp[DraftPositionConstants.PLAYER] += cnt
    return cnt_dp

def stats_by_dp(keys: Keys | KeyGroups, get_dp: KeysReader | Callable[[str], str | None]) -> dict[str, dict[str, int]]:
    dp_cnt = count_by_dp(keys, get_dp)
    dp_stats: dict[str, dict[str, int]] = {}
    deficit = False
    surplus = False
    for dp, cnt_dp in dp_cnt.items():
        limits = DraftPositionConstants.LIMITS[dp]
        dp_stats[dp] = {"cnt": cnt_dp, "min": limits["min"], "max": limits["max"]}
        if dp not in {DraftPositionConstants.PLAYER, DraftPositionConstants.MEMBER}:
            dp_stats[dp]["must_add"] = max(limits["min"] - cnt_dp, 0)
            dp_stats[dp]["must_remove"] = max(cnt_dp - limits["max"], 0)
            dp_stats[dp]["can_add"] = max(limits["max"] - cnt_dp, 0)
            dp_stats[dp]["can_remove"] = max(cnt_dp - limits["min"], 0)
            deficit = deficit or dp_stats[dp]["must_add"] > 0
            surplus = surplus or dp_stats[dp]["must_remove"] > 0
    dp_stats[DraftPositionConstants.MEMBER]["deficit"] = deficit
    dp_stats[DraftPositionConstants.MEMBER]["surplus"] = surplus
    return dp_stats


class MemberKeys(Keys):
    def __init__(
        self,
        get_dp: KeysReader | Callable[[str], str | None],
    ) -> None:
        self._get_dp = get_dp.get_dp if hasattr(get_dp, "get_dp") else get_dp
        super().__init__(allow_dups=False)

    def get_add_drops(self, keys) -> tuple[list[str], list[str]]:
        keys_list = Keys.to_list(keys) or []
        current_set = set(self.data)
        to_add = [k for k in keys_list if k not in current_set]
        to_drop = [k for k in keys_list if k in current_set]
        return (to_add, to_drop)

    def try_change(self, to_add: list, to_drop: list) -> bool:
        adding = {k: self._get_dp(k) for k in to_add}
        dropping = {k: self._get_dp(k) for k in to_drop}
        before = count_by_dp(self, self._get_dp)
        after = before.copy()
        keys = self.data.copy()
        keys_set = set(keys)
        for k, dp in dropping.items():
            if not dp:
                raise ValueError
            if k not in keys_set:
                return False
            after[dp] = after.get(dp, 0) - 1
            keys.remove(k)
            keys_set.remove(k)
        for k, dp in adding.items():
            if not dp:
                raise ValueError
            if k in keys_set:
                return False
            after[dp] = after.get(dp, 0) + 1
            keys.append(k)
            keys_set.add(k)
        if self._valid(after):
            self.data = keys
            return True
        return False

    def _valid(self, cnt: dict[str, int]) -> bool:
        return all(
            DraftPositionConstants.check_bounds(dp, n) == 0
            for dp, n in cnt.items()
            if dp in DraftPositionConstants.LIMITS
        )


class DraftingKeys(Keys):
    """Keys with draft-position awareness: dp_cnt, dp_stats, and available_dp."""

    def __init__(
        self,
        get_dp: KeysReader | Callable[[str], str | None],
        allow_dups: bool | None = False,
    ) -> None:
        self._get_dp = get_dp.get_dp if hasattr(get_dp, "get_dp") else get_dp
        super().__init__(allow_dups=allow_dups)

    @property
    def dp_cnt(self) -> dict[str, int]:
        return count_by_dp(self, self._get_dp)

    @property
    def dp_stats(self) -> dict[str, dict[str, int]]:
        dp_cnt = self.dp_cnt
        dp_stats: dict[str, dict[str, int]] = {}
        deficit = False
        surplus = False
        for dp, cnt_dp in dp_cnt.items():
            limits = DraftPositionConstants.LIMITS[dp]
            dp_stats[dp] = {"cnt": cnt_dp, "min": limits["min"], "max": limits["max"]}
            if dp not in {DraftPositionConstants.PLAYER, DraftPositionConstants.MEMBER}:
                dp_stats[dp]["must_add"] = max(limits["min"] - cnt_dp, 0)
                dp_stats[dp]["must_remove"] = max(cnt_dp - limits["max"], 0)
                dp_stats[dp]["can_add"] = max(limits["max"] - cnt_dp, 0)
                dp_stats[dp]["can_remove"] = max(cnt_dp - limits["min"], 0)
                deficit = deficit or dp_stats[dp]["must_add"] > 0
                surplus = surplus or dp_stats[dp]["must_remove"] > 0
        dp_stats[DraftPositionConstants.MEMBER]["deficit"] = deficit
        dp_stats[DraftPositionConstants.MEMBER]["surplus"] = surplus
        return dp_stats

    @property
    def is_valid(self) -> bool:
        dp_stats = self.dp_stats
        return (
            not dp_stats[DraftPositionConstants.MEMBER]["deficit"]
            and not dp_stats[DraftPositionConstants.MEMBER]["surplus"]
        )

    def available_dp(self, draft_lowest: bool) -> set[str]:
        dp_cnt = self.dp_cnt
        available: set[str] = set()
        if draft_lowest:
            for dp, limits in DraftPositionConstants.LIMITS.items():
                if (
                    dp
                    not in {
                        DraftPositionConstants.PLAYER,
                        DraftPositionConstants.MEMBER,
                    }
                    and dp_cnt.get(dp, 0) < limits["lowest"]
                ):
                    available.add(dp)
        if not available:
            dp_stats = self.dp_stats
            cnt_must = 0
            can_add_dp: set[str] = set()
            for dp, stats in dp_stats.items():
                if dp not in {
                    DraftPositionConstants.PLAYER,
                    DraftPositionConstants.MEMBER,
                }:
                    if stats["must_add"] > 0:
                        cnt_must += stats["must_add"]
                        available.add(dp)
                    elif stats["can_add"] > 0:
                        can_add_dp.add(dp)
            if (
                dp_stats[DraftPositionConstants.MEMBER]["cnt"] + cnt_must
                < dp_stats[DraftPositionConstants.MEMBER]["max"]
            ):
                available.update(can_add_dp)
        return available


def _keys_str_to_list(txt: str) -> list[str]:
    stripped = txt.replace(Keys.SUFFIX, "").replace(Keys._SUFFIX, "").replace(" ", "")
    if not stripped:
        return []
    return (
        stripped.replace(Keys.PLAYER, " " + Keys.PLAYER)
        .replace(Keys.TEAM, " " + Keys.TEAM)[1:]
        .split(" ")
    )


def _keys_list_to_str(items: list[str]) -> str:
    return Keys.SUFFIX.join(items) + Keys.SUFFIX if len(items) > 0 else ""
