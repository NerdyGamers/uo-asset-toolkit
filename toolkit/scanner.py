# toolkit/scanner.py
# Scans all asset types across a client, building a complete snapshot.

from typing import List, Dict, Optional, Callable
from .asset_registry import AssetRegistry
from .client import UOClient


class ScanResult:
    def __init__(self, asset_type: str, asset_id: int, data: Optional[bytes]):
        self.asset_type = asset_type
        self.asset_id = asset_id
        self.data = data
        self.found = data is not None


class Scanner:
    """
    Iterates over all asset IDs in a registry and reads raw data from the client.
    Supports an optional progress callback: callback(current, total).
    """

    def __init__(self, client: UOClient, registry: AssetRegistry):
        self.client = client
        self.registry = registry

    def scan_art(
        self,
        reader_fn: Callable[[int], Optional[bytes]],
        progress_cb: Optional[Callable[[int, int], None]] = None,
    ) -> List[ScanResult]:
        ids = self.registry.all_ids()
        total = len(ids)
        results = []

        for i, asset_id in enumerate(ids):
            data = reader_fn(asset_id)
            results.append(ScanResult("art", asset_id, data))
            if progress_cb:
                progress_cb(i + 1, total)

        return results

    def scan_gumps(
        self,
        reader_fn: Callable[[int], Optional[bytes]],
        progress_cb: Optional[Callable[[int, int], None]] = None,
    ) -> List[ScanResult]:
        ids = self.registry.all_ids()
        total = len(ids)
        results = []

        for i, asset_id in enumerate(ids):
            data = reader_fn(asset_id)
            results.append(ScanResult("gump", asset_id, data))
            if progress_cb:
                progress_cb(i + 1, total)

        return results
