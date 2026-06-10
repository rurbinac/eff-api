from __future__ import annotations
from typing import Any, Final, Iterator, TypeAlias, overload

GroupData: TypeAlias = list[str]
PackedData: TypeAlias = list[GroupData]


class MKeys:
    """Manages hierarchical keys with group separation.

    Format: "group1.key1.key2.:group2.key3.:"
    - Keys must start with 'P' or 'T' followed by a number
    - Groups separated by ':'
    - Keys within groups separated by '.'
    - Each group must end with '.'
    """

    DELIM: Final[str] = ":"
    SUFFIX: Final[str] = "."

    @staticmethod
    def split_key(key: Any) -> tuple[str, int] | tuple[None, None]:
        """Splits a key into its type (first character) and number (rest of the string).
        Returns (type, number) if valid, (None, None) if invalid."""
        if isinstance(key, str):
            k = key.strip()
            if len(k) > 1:
                if k.startswith("T") or k.startswith("P"):
                    try:
                        num = int(k[1:])
                        if num > 0:
                            return (k[0:1], num)
                    except ValueError:
                        pass
        return (None, None)

    @staticmethod
    def valid_key(key: Any) -> bool:
        """Returns True if the key is valid, False otherwise."""
        return MKeys.split_key(key)[0] is not None

    @classmethod
    def build(
        cls,
        data: str | PackedData | None = None,
        size: int | None = None,
        allow_dups: bool | None = False,
    ) -> MKeys | None:
        """Builds an MKeys instance from the given data. Returns the instance if successful, None if invalid."""
        instance = cls(allow_dups)
        instance.unpack(data, size)
        return instance if instance.is_valid else None

    def __init__(self, allow_dups: bool | None = False) -> None:
        """Initializes the MKeys instance.
        If allow_dups is:
        - True, duplicate keys are allowed.
        - False, duplicate keys are not allowed (the first occurrence will be used, the duplicates will cause an error).
        - None, duplicate keys are ignored (the first occurrence will be used, the duplicates will be discarded).
        Duplicates are verified across all groups."""
        self._allow_dups = allow_dups  # If dups is None, it will ignore dups (the first key will be used, the dups discarded)
        self._groups: PackedData | None = None

    @property
    def dups(self) -> bool | None:
        """Returns the duplicates handling mode:
        - True if duplicates are allowed
        - False if duplicates are not allowed
        - None if duplicates are ignored (only the first occurrence is used)."""
        return self._allow_dups

    @property
    def is_valid(self) -> bool:
        """Returns:
        - True if the groups are valid
        - False otherwise."""
        return isinstance(self._groups, list)

    @property
    def is_empty(self) -> bool:
        """Returns True if there are no keys in any group."""
        return len(self) == 0 if self.is_valid else True

    def unpack(
        self, data: str | PackedData | None = None, size: int | None = None
    ) -> bool:
        """Initializes the MKeys instance by unpacking the given data into groups.
        Data can be a string in the packed format or a list of groups (where each group is a list of keys).
        If data is None, it will clear all groups.
        If size is provided, it will ensure that the number of groups matches the size.
        Returns:
        - True if successful
        - False if invalid.
        """
        #
        self._groups = []  # Reset groups before unpacking, so that we can build the set of all keys from scratch
        # Initial unpacking and validation of the input data
        if isinstance(data, list):
            txt = self._repack(data)
            if txt is None:
                return False
        elif isinstance(data, str):
            txt = data.strip()
        elif data is None:
            txt = ""
        else:
            return False
        if txt == "":
            # No data is valid (size validation will handle the case where size is provided but data is empty)
            unpacked = []
        else:
            # Split groups by ':', but only if data is not empty
            # (otherwise we would get a single group with an empty string, which is not what we want)
            unpacked = txt.split(MKeys.DELIM)
        # Validate the size
        if size is not None:
            if size <= 0:
                # Invalid size
                return False
            if len(unpacked) != size and len(unpacked) > 0:
                # Size mismatch
                return False
            if len(unpacked) == 0:
                # If size is provided but data is empty, we will create empty groups
                # This is a special case to allow creating empty groups by providing a size but no data
                unpacked = [""] * size
        # Parse each group and build the set of all keys
        all_keys: set[str] = set()
        groups: PackedData = []
        for txt in unpacked:
            group_keys, all_keys = self._unpack_group(txt, all_keys)
            if group_keys is None:
                return False
            groups.append(group_keys)
        # Done
        self._groups = groups
        return True

    def pack(self) -> str:
        """Returns the packed string representation of the groups, or an empty string if invalid."""
        if self.is_valid:
            groups = []
            for g in self._groups:
                groups.append(self._pack_list(g))
            return MKeys.DELIM.join(groups)
        return ""

    @property
    def size(self) -> int:
        """Returns the number of groups, or 0 if invalid."""
        return len(self._groups) if self.is_valid else 0

    def has_group(self, group: int = 0) -> bool:
        """Returns True if the specified group exists, False otherwise."""
        return self.is_valid and group >= 0 and group < len(self._groups)

    def get_groups(self) -> PackedData:
        """Returns a copy of the list of groups, where each group is a list of keys.
        Returns an empty list if invalid."""
        return [g.copy() for g in self._groups] if self.is_valid else []

    def get_group(self, group: int = 0) -> list[str]:
        """Returns a copy of the list of keys in the specified group,
        or an empty list if the group does not exist."""
        return self._groups[group].copy() if self.has_group(group) else []

    def set_group(self, data: str | list | None = None, group: int = 0) -> bool:
        """Sets the keys in the specified group. The group must already exist.
        Returns:
        - True if successful
        - False if invalid."""
        if not self.has_group(group):
            return False
        keys = self._check_new_keys(data, group)
        if keys is None:
            # Error unpacking
            return False
        # Done
        self._groups[group] = keys
        return True

    def remove_group(self, group: int) -> bool:
        """Remove the specified group. Returns True if successful."""
        if not self.has_group(group):
            return False
        del self._groups[group]
        return True

    def append_group(self, data: str | list | None = None) -> bool:
        """Append a new group at the end."""
        keys = self._check_new_keys(data)
        if keys is None:
            # Error unpacking
            return False
        # Done
        if self._groups is None:
            self._groups = []
        self._groups.append(keys)
        return True

    def insert_group(self, group: int, data: str | list | None = None) -> bool:
        """Insert a new group at the specified index. Works as the insert method of lists,
        so if group is greater than the number of groups, it will append the new group at the end,
        also handles negative indices."""
        keys = self._check_new_keys(data)
        if keys is None:
            # Error unpacking
            return False
        # Done
        if self._groups is None:
            self._groups = []
        self._groups.insert(group, keys)
        return True

    def clear(self) -> None:
        """Clear all groups contents, preserving the number of groups."""
        if self.is_valid:
            self._groups = [[] for _ in range(len(self._groups))]

    def count(self, group: int = 0) -> int | None:
        """Returns the number of keys in the specified group, or None if the group does not exist."""
        return len(self._groups[group]) if self.has_group(group) else None

    def find_group(self, key: str) -> int:
        """Returns the index of the group containing the key, or -1 if not found or invalid."""
        if self.is_valid:
            for i, keys in enumerate(self._groups):
                if key in keys:
                    return i
        return -1

    def has_key(self, key: str, group: int | None = None) -> bool:
        """Returns:
        - True if the key exists in the specified group (or any group if group is None)
        - False otherwise."""
        if group is None:
            return self.find_group(key) >= 0
        else:
            return self.has_group(group) and key in self._groups[group]

    def get_key(self, i: int, group: int = 0) -> str | None:
        """Returns:
        - The key at index i in the specified group
        - None if the group or index is invalid."""
        if self.has_group(group) and i >= 0 and i < len(self._groups[group]):
            return self._groups[group][i]
        return None

    def pop_first_key(self, group: int = 0) -> str | None:
        """Returns:
        - The first key in the specified group
        - None if the group is invalid or empty."""
        if self.has_group(group) and self.count(group) > 0:
            return self._groups[group].pop(0)
        return None

    def pop_last_key(self, group: int = 0) -> str | None:
        """Returns:
        - The last key in the specified group
        - None if the group is invalid or empty."""
        if self.has_group(group) and self.count(group) > 0:
            return self._groups[group].pop()
        return None

    def append_key(self, key: str, group: int = 0) -> bool:
        """Appends a key to the specified group.
        Returns:
        - True if successful
        - False if invalid or if duplicates are not allowed (allow_dups=False|None)
          and the key already exists in ANY group."""
        if self.has_group(group) and self.valid_key(key):
            if self._allow_dups is True or self.find_group(key) < 0:
                # Append if duplicates are allowed or the key does not exist in any group
                self._groups[group].append(key)
                return True
        return False

    def remove_key(self, key: str, group: int | None = None) -> bool:
        """Removes a key from the specified group or all groups (if group is None).
        Returns:
        - True if successful
        - False if invalid or if the key does not exist in the group."""
        if group is None:
            # Remove from all groups
            found = False
            for g in self._groups:
                if key in g:
                    g.remove(key)
                    found = True
            return found
        elif self.has_group(group) and key in self._groups[group]:
            self._groups[group].remove(key)
            return True
        return False

    def move_key(self, key: str, from_group: int, to_group: int) -> bool:
        """Moves a key from one group to another.

        Note: With global duplicate checking, this operation is always safe
        since if the key can be in a group then it can be moved to any other
        group without breaking the duplicate constraint.

        Returns:
        - True if successful
        - False if invalid or if the key does not exist in the from_group
        """
        if (
            self.has_group(from_group)
            and self.has_group(to_group)
            and key in self._groups[from_group]
        ):
            if from_group != to_group:
                # Since key is in from_group, it was checked for duplicates against all groups,
                # so we can move it to to_group without checking for duplicates again.
                self._groups[from_group].remove(key)
                self._groups[to_group].append(key)
            return True
        return False

    def copy(self) -> MKeys:
        """Returns a deep copy of the MKeys instance."""
        new = MKeys(self._allow_dups)
        if self.is_valid:
            new._groups = [g.copy() for g in self._groups]
        return new

    @overload
    def keys(self, group: int) -> Iterator[str]: ...
    @overload
    def keys(self, group: None = None) -> Iterator[tuple[int, str]]: ...

    def keys(
        self, group: int | None = None
    ) -> Iterator[str] | Iterator[tuple[int, str]]:
        """Returns an iterator over keys.
        If group is specified, iterates over keys in that group.
        If group is None, iterates over all keys in all groups."""
        if group is None:
            for i, g in enumerate(self._groups):
                for key in g:
                    yield i, key
        elif self.has_group(group):
            yield from self._groups[group]

    def __str__(self) -> str:
        """Returns:
        - The packed string representation of the groups
        - An empty string if invalid."""
        return self.pack()

    def __repr__(self) -> str:
        """Return a string representation of the MKeys instance."""
        return f"MKeys(allow_dups={self._allow_dups}, groups={self._groups})"

    def __len__(self) -> int:
        """Returns the total number of keys across all groups."""
        return sum(len(g) for g in self._groups) if self.is_valid else 0

    def _repack(
        self, data: list[str] | list[list], recursive: bool = True
    ) -> str | None:
        """Repack data from list form to string form.
        If recursive is False, it will only repack a single group (list of strings)."""
        if not data:
            return ""
        if all(isinstance(x, str) for x in data):
            if all(self.valid_key(x) for x in data):
                # The main case data is a single group
                return self._pack_list(data)
            else:
                return None
        if not recursive or not all(isinstance(x, list) for x in data):
            return None
        # Check if data is several groups
        parts = []
        for d in data:
            packed = self._repack(d, False)
            # A valid d can only return a string, since recursive=False
            if isinstance(packed, str):
                parts.append(packed)
            else:
                return None
        return MKeys.DELIM.join(parts)

    def _unpack_group(
        self, txt: str, all_keys: set[str]
    ) -> tuple[list[str] | None, set[str]]:
        """Unpack a single group from string form to list form, while checking for duplicates against all_keys.
        Returns (keys, all_keys) where
        - keys is the list of keys in the group (or None if invalid)
        - all_keys is the updated set of all keys seen so far."""
        txt = txt.strip()
        if txt == "":
            # Empty group
            return ([], all_keys)
        if not txt.endswith(MKeys.SUFFIX):
            # All keys end with a dot
            return (None, all_keys)
        # Load each key in Keys
        keys = []
        for k in txt[:-1].split(MKeys.SUFFIX):
            if not self.valid_key(k):
                return (None, all_keys)
            if k not in all_keys:
                # New key, just add it to list and set
                keys.append(k)
                all_keys.add(k)
            elif self._allow_dups is False:
                # Duplicate key and duplicates not allowed
                return (None, all_keys)  # Fail
            elif self._allow_dups is True:
                # Duplicate key and duplicates allowed
                keys.append(k)
            elif self._allow_dups is None:
                # Duplicate key and duplicates ignored
                continue  # Do nothing
        return (keys, all_keys)

    def _pack_list(self, data: list[str]) -> str:
        """Pack a list of keys into a string, adding the suffix at the end.
        Returns an empty string if data is empty."""
        return self.SUFFIX.join(data) + self.SUFFIX if data else ""

    def _check_new_keys(
        self, data: str | list | None = None, group: int | None = None
    ) -> list[str] | None:
        """Checks the new keys to be added for a group, ensuring they are valid and do not cause duplicates (if not allowed).
         If group is specified, it will check for duplicates against all groups except the specified one
         (to allow changing the keys in a group without causing false duplicates with itself).
         Returns:
        - the list of keys if valid
        - None if invalid."""
        # Initialize data_str based on the type of data
        if data is None:
            data_str = ""
        elif isinstance(data, list):
            if len(data) == 0:
                data_str = ""
            else:
                # Transform data to packed form
                data_str = self._repack(data, False)
                if not isinstance(data_str, str):
                    # data was not list[str]
                    return None
        elif isinstance(data, str):
            data_str = data.strip()
        else:
            return None
        # Get the set of all keys from all groups except the current one (if group is specified), to check for duplicates
        all_keys = set()
        if self.is_valid:
            for g, k in enumerate(self._groups):
                if group is None or g != group:
                    all_keys.update(k)
        keys, _ = self._unpack_group(data_str, all_keys)
        return keys  # Will be None if there was an error unpacking (invalid keys or duplicates not allowed)


class FantasyTeamMembers:
    """Manages fantasy team members with position tracking using MKeys.

    Stores team members (players and coaches) with their draft positions.
    Maps member keys to draft positions: {'P123': '1', 'P456': '2', etc.}
    """

    def __init__(self, allow_dups: bool = False) -> None:
        """Initialize an empty fantasy team.

        Args:
            allow_dups: Whether to allow duplicate members
        """
        self._mkeys = MKeys(allow_dups)
        self._mkeys.unpack(None, 1)  # Single group for all team members
        self._positions: dict[str, str] = {}  # Maps member_key -> draft_position

    @property
    def total_members(self) -> int:
        """Return total number of members on team."""
        return len(self._mkeys)

    def is_valid(self) -> bool:
        """Check if team structure is valid."""
        return self._mkeys.is_valid

    def get_members(self) -> list[str]:
        """Get all members on team."""
        return self._mkeys.get_group(0)

    def get_positions(self) -> dict[str, str]:
        """Get mapping of member keys to draft positions."""
        return self._positions.copy()

    def add_member(self, member_key: str, position: str = "") -> bool:
        """Add a single member with optional draft position.

        Args:
            member_key: Member key (e.g., 'P123')
            position: Draft position (e.g., '1', '2', etc.)

        Returns:
            True if successful, False if invalid or duplicate
        """
        if self._mkeys.append_key(member_key, 0):
            self._positions[member_key] = position
            return True
        return False

    def add_members(self, members: dict[str, str] | list[str]) -> int:
        """Add multiple members at once.

        Args:
            members: Dict mapping member_key -> position, or list of keys
                    (positions default to empty string)

        Returns:
            Number of members successfully added
        """
        added = 0
        if isinstance(members, dict):
            for key, position in members.items():
                if self.add_member(key, position):
                    added += 1
        elif isinstance(members, list):
            for key in members:
                if self.add_member(key):
                    added += 1
        return added

    def remove_member(self, member_key: str) -> bool:
        """Remove a single member."""
        if self._mkeys.remove_key(member_key, 0):
            self._positions.pop(member_key, None)
            return True
        return False

    def remove_members(self, member_keys: list[str]) -> int:
        """Remove multiple members at once.

        Args:
            member_keys: List of member keys to remove

        Returns:
            Number of members successfully removed
        """
        removed = 0
        for key in member_keys:
            if self.remove_member(key):
                removed += 1
        return removed

    def has_member(self, member_key: str) -> bool:
        """Check if member exists on team."""
        return self._mkeys.has_key(member_key, 0)

    def get_position(self, member_key: str) -> str:
        """Get draft position for a member. Returns empty string if not found."""
        return self._positions.get(member_key, "")

    def set_position(self, member_key: str, position: str) -> bool:
        """Update draft position for a member."""
        if self.has_member(member_key):
            self._positions[member_key] = position
            return True
        return False

    def get_by_position(self, position: str) -> list[str]:
        """Get all members with a specific draft position."""
        return [k for k, pos in self._positions.items() if pos == position]

    def get_players(self) -> list[str]:
        """Get all players (P*) on team."""
        return [k for k in self.get_members() if k.startswith('P')]

    def get_coaches(self) -> list[str]:
        """Get all coaches/staff (T*) on team."""
        return [k for k in self.get_members() if k.startswith('T')]

    def count_members(self) -> int:
        """Count total members on team."""
        return self.total_members

    def count_players(self) -> int:
        """Count players (P*) on team."""
        return len(self.get_players())

    def count_coaches(self) -> int:
        """Count coaches/staff (T*) on team."""
        return len(self.get_coaches())

    def clear(self) -> None:
        """Clear all members from team."""
        self._mkeys.clear()
        self._positions.clear()

    def to_packed_string(self) -> str:
        """Export member keys as packed string format."""
        return self._mkeys.pack()

    def from_packed_string(self, data: str) -> bool:
        """Import member keys from packed string format. Preserves positions."""
        if self._mkeys.unpack(data, 1):
            # Keep existing positions for members that are still there
            # Remove positions for members that are no longer there
            current_members = set(self.get_members())
            self._positions = {k: v for k, v in self._positions.items() if k in current_members}
            return True
        return False

    def copy(self) -> "FantasyTeamMembers":
        """Create a deep copy of team members."""
        new_team = FantasyTeamMembers(self._mkeys.dups is True)
        new_team._mkeys = self._mkeys.copy()
        new_team._positions = self._positions.copy()
        return new_team

    def __str__(self) -> str:
        """String representation of team."""
        return f"FantasyTeamMembers(members={self.total_members}, players={self.count_players()}, coaches={self.count_coaches()})"

    def __repr__(self) -> str:
        """Detailed representation."""
        return f"FantasyTeamMembers(members={self.get_members()}, positions={self._positions})"
