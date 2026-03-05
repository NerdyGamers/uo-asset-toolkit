# toolkit/cache.py
# Disk-based hash cache to skip re-scanning unchanged assets.

import os
import json
from typing import Dict, Optional


class AssetCache:
    """
    Persists asset hashes to a JSON file on disk.
    On next run, unchanged assets skip re-processing.
    """

    def __init__(self, cache_path: str):
        self.cache_path = cache_path
        self._data: Dict[str, str] = {}
        self._dirty = False
        self._load()

    def _load(self):
        if os.path.isfile(self.cache_path):
            try:
                with open(self.cache_path, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._data = {}

    def get(self, key: str) -> Optional[str]:
        """Retrieve cached hash for a key (e.g. 'art_0x1A34')."""
        return self._data.get(key)

    def set(self, key: str, hash_val: str):
        """Store a hash for a key. Marks cache dirty."""
        if self._data.get(key) != hash_val:
            self._data[key] = hash_val
            self._dirty = True

    def is_changed(self, key: str, new_hash: Optional[str]) -> bool:
        """Returns True if new_hash differs from cached value."""
        return self._data.get(key) != new_hash

    def save(self):
        """Flush cache to disk if dirty."""
        if not self._dirty:
            return
        os.makedirs(os.path.dirname(self.cache_path) or ".", exist_ok=True)
        with open(self.cache_path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2)
        self._dirty = False

    def clear(self):
        """Wipe the in-memory cache and mark dirty."""
        self._data = {}
        self._dirty = True

    def __len__(self) -> int:
        return len(self._data)
