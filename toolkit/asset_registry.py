# toolkit/asset_registry.py
# Builds a registry of all valid asset IDs from the client index files.
# Smart scan: only IDs present in the index are registered (no empty slot spam).

import os
import struct
from typing import Dict, List, Optional


class AssetEntry:
    __slots__ = ("asset_id", "offset", "length", "extra")

    def __init__(self, asset_id: int, offset: int, length: int, extra: int = 0):
        self.asset_id = asset_id
        self.offset = offset
        self.length = length
        self.extra = extra

    def is_valid(self) -> bool:
        return self.offset != 0xFFFFFFFF and self.length > 0


class AssetRegistry:
    """
    Reads the MUL index file (.idx) and builds a fast lookup of
    all valid asset IDs. Falls back to range scan if no index exists.
    """

    IDX_ENTRY_SIZE = 12  # offset(4) + length(4) + extra(4)

    def __init__(self):
        self._entries: Dict[int, AssetEntry] = {}

    def load_from_idx(self, idx_path: str) -> int:
        """Load asset registry from a MUL .idx file. Returns count of valid entries."""
        if not os.path.isfile(idx_path):
            raise FileNotFoundError(f"Index file not found: {idx_path}")

        count = 0
        with open(idx_path, "rb") as f:
            asset_id = 0
            while True:
                raw = f.read(self.IDX_ENTRY_SIZE)
                if len(raw) < self.IDX_ENTRY_SIZE:
                    break
                offset, length, extra = struct.unpack("<III", raw)
                entry = AssetEntry(asset_id, offset, length, extra)
                if entry.is_valid():
                    self._entries[asset_id] = entry
                    count += 1
                asset_id += 1
        return count

    def load_range(self, start: int, end: int):
        """Populate registry with a synthetic range (fallback for UOP clients)."""
        for i in range(start, end):
            self._entries[i] = AssetEntry(i, 0, 1)

    def get(self, asset_id: int) -> Optional[AssetEntry]:
        return self._entries.get(asset_id)

    def all_ids(self) -> List[int]:
        return sorted(self._entries.keys())

    def count(self) -> int:
        return len(self._entries)

    def __contains__(self, asset_id: int) -> bool:
        return asset_id in self._entries
