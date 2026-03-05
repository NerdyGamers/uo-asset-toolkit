# toolkit/diff_engine.py
# Compares assets between clean and modded clients using hash comparison.

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from .hashing import hash_asset, assets_differ


@dataclass
class DiffResult:
    asset_id: int
    asset_type: str          # 'art', 'gump', 'texture', etc.
    clean_hash: Optional[str]
    modded_hash: Optional[str]
    status: str              # 'modified' | 'added' | 'removed' | 'identical'

    @property
    def is_changed(self) -> bool:
        return self.status != 'identical'


class DiffEngine:
    """
    Compares raw asset bytes between two clients and returns a list of DiffResults.
    """

    def __init__(self, algorithm: str = "sha256"):
        self.algorithm = algorithm

    def diff_asset(
        self,
        asset_id: int,
        asset_type: str,
        clean_data: Optional[bytes],
        modded_data: Optional[bytes],
    ) -> DiffResult:
        clean_hash = hash_asset(clean_data, self.algorithm)
        modded_hash = hash_asset(modded_data, self.algorithm)

        if clean_data is None and modded_data is not None:
            status = "added"
        elif clean_data is not None and modded_data is None:
            status = "removed"
        elif assets_differ(clean_hash, modded_hash):
            status = "modified"
        else:
            status = "identical"

        return DiffResult(
            asset_id=asset_id,
            asset_type=asset_type,
            clean_hash=clean_hash,
            modded_hash=modded_hash,
            status=status,
        )

    def diff_batch(
        self,
        asset_type: str,
        pairs: List[Tuple[int, Optional[bytes], Optional[bytes]]],
    ) -> List[DiffResult]:
        """Diff a batch of (asset_id, clean_data, modded_data) tuples."""
        results = []
        for asset_id, clean_data, modded_data in pairs:
            result = self.diff_asset(asset_id, asset_type, clean_data, modded_data)
            results.append(result)
        return results

    def filter_changed(self, results: List[DiffResult]) -> List[DiffResult]:
        """Return only results where the asset changed."""
        return [r for r in results if r.is_changed]
