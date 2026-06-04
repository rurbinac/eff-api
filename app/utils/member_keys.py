from typing import Any

class MKeys:
    """Manages hierarchical keys with group separation.
    
    Format: "group1.key1.key2.:group2.key3.:"
    - Keys must start with 'P' or 'T' followed by a number
    - Groups separated by ':'
    - Keys within groups separated by '.'
    - Each group must end with '.'
    """
    @staticmethod
    def split_key(key: Any) -> tuple[str | None, int | None]:
        if isinstance(key, str):
            k = key.strip()
            if len(k) > 1:
                if k.startswith("T") or k.startswith("P"):
                    try:
                        num = int(k[1:])
                        return (k[0:1], num)
                    except ValueError:
                        pass
        return (None, None)
    
    @staticmethod
    def valid_key(key: Any) -> bool:
        t, n = MKeys.split_key(key)
        return isinstance(t, str) and isinstance(n, int)
    
    def __init__(self, txt: str, size: int | None = None, dups: bool | None = False) -> None:
        self._dups = dups # If dups is None, it will ignore dups (the first key will be used, the dups discarded)
        self._keys: tuple[list[str], ...] | None = None
        self.unpack(txt, size)
        
    @property
    def is_valid(self) -> bool:
        return isinstance(self._keys, tuple)
        
    def unpack(self, txt: str, size: int | None = None) -> bool:
        keys = txt.split(":")
        all_keys = set()
        for i in range(len(keys)):
            keys[i] = keys[i].strip()
            if keys[i].endswith("."):
                keys[i] = keys[i][0:-1]
            else:
                return False
            if keys[i] == "":
                keys[i] = []
            else:
                ks = keys[i].split(".")
                keys[i] = []
                for k in ks:
                    if not self.valid_key(k):
                        return False
                    if k not in all_keys:
                        # New key, just add it to list and set
                        keys[i].append(k)
                        all_keys.add(k)
                    elif self._dups is True:
                        # Duplicate key and duplicates allowed
                        keys[i].append(k)  
                    elif self._dups is False:
                        # Duplicate key and duplicates not allowed
                        return False  # Fail
                    elif self._dups is None:
                        # Duplicate key and duplicates ignored
                        pass # Do nothing                        
        if size is None:
            size = len(keys)
        while len(keys) < size:
            keys.append([])
        self._keys = tuple(keys)
        return True

    def pack(self) -> str:
        if self.is_valid:
            keys = []
            for k in self._keys:
                keys.append(".".join(k) + "." if len(k) > 0 else "")
            return ":".join(keys)
        return ""
    
    @property
    def size(self) -> int:
        return len(self._keys) if self.is_valid else 0
        
    def count(self, g: int = 0) -> int | None:
        return len(self._keys[g]) if self.is_valid and g >= 0 and g < len(self._keys) else None
        
    def find_group(self, key: str) -> int:
        if self.is_valid:
            for i, keys in enumerate(self._keys):
                if key in keys:
                    return i
        return -1

    def get_key(self, i: int, g: int = 0) -> str | None:
        if self.is_valid:
            cnt = self.count(g)
            if cnt is not None and i >= 0 and i < cnt:
                return self._keys[g][i]
        return None
