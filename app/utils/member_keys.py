from __future__ import annotations
from typing import Any, Final, TypeAlias

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
        If allow_dups is True, duplicate keys are allowed.
        If allow_dups is False, duplicate keys are not allowed (the first occurrence will be used, the duplicates will cause an error).
        If allow_dups is None, duplicate keys are ignored (the first occurrence will be used, the duplicates will be discarded)."""
        self._allow_dups = allow_dups  # If dups is None, it will ignore dups (the first key will be used, the dups discarded)
        self._groups: PackedData | None = None

    @property
    def dups(self) -> bool | None:
        """Returns the duplicates handling mode: True if duplicates are allowed, False if duplicates are not allowed, None if duplicates are ignored."""
        return self._allow_dups

    @property
    def is_valid(self) -> bool:
        """Returns True if the groups are valid, False otherwise."""
        return isinstance(self._groups, list)

    def has_group(self, group: int = 0) -> bool:
        """Returns True if the specified group exists, False otherwise."""
        return self.is_valid and group >= 0 and group < len(self._groups)

    def get_groups(self) -> PackedData:
        """Returns a copy of the list of groups, where each group is a list of keys. Returns an empty list if invalid."""
        return [g.copy() for g in self._groups] if self.is_valid else []

    def get_group(self, group: int = 0) -> list[str]:
        """Returns a copy of the list of keys in the specified group, or an empty list if the group does not exist."""
        return self._groups[group].copy() if self.has_group(group) else []

    def set_group(self, data: str | list | None = None, group: int = 0) -> bool:
        """Sets the keys in the specified group.
        Returns True if successful, False if invalid.
        The group must already exist."""
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

    def unpack(
        self, data: str | PackedData | None = None, size: int | None = None
    ) -> bool:
        """Unpacks the given data into groups. Data can be a string in the packed format or a list of groups (where each group is a list of keys).
        Returns True if successful, False if invalid.
        If size is provided, it will ensure that the number of groups matches the size.
        If data is None, it will clear all groups."""
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
            # No data, no groups, is treated as valid (size validation will handle the case where size is provided but data is empty)
            unpacked = []
        else:
            # Split groups by ':', but only if data is not empty (otherwise we would get a single group with an empty string, which is not what we want)
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
        """Returns True if the key exists in the specified group (or any group if group is None), False otherwise."""
        g = self.find_group(key)
        return g >= 0 and (group is None or group == g)

    def get_key(self, i: int, group: int = 0) -> str | None:
        """Returns the key at index i in the specified group, or None if the group or index is invalid."""
        if self.has_group(group):
            if i >= 0 and i < len(self._groups[group]):
                return self._groups[group][i]
        return None

    def __str__(self) -> str:
        """Returns the packed string representation of the groups, or an empty string if invalid."""
        return self.pack()

    def __repr__(self) -> str:
        """Return a string representation of the MKeys instance."""
        return f"MKeys(allow_dups={self._allow_dups}, groups={self._groups})"

    def _repack(self, data: list, recursive: bool = True) -> str | None:
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

    def _unpack_group(self, txt: str, all_keys: set) -> tuple[list | None, set]:
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
        """Pack a list of keys into a string, adding the suffix at the end. Returns an empty string if data is empty."""
        return self.SUFFIX.join(data) + self.SUFFIX if data else ""

    def _check_new_keys(
        self, data: str | list | None = None, group: int | None = None
    ) -> list[str] | None:
        """Checks the new keys for a group, ensuring they are valid and do not cause duplicates (if not allowed)."""
        if data is None:
            data_str = ""
        elif isinstance(data, list):
            # Transform data to packed form
            data_str = self._repack(data, False)
            if not isinstance(data_str, str):
                # data was not list[str]
                return None
        elif isinstance(data, str):
            data_str = data
        else:
            return None
        all_keys = set()
        if self.is_valid:
            for g, k in enumerate(self._groups):
                if group is None or g != group:
                    all_keys.update(k)
        keys, _ = self._unpack_group(data_str, all_keys)
        return keys
