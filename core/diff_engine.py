"""
core/diff_engine.py - Compare mod assets against the vanilla UO client

Usage
-----
engine = DiffEngine(client_path)
result = engine.diff_asset(asset_id, asset_type, clean_bytes, modded_bytes)
result.is_changed   -> bool
result.change_type  -> str   ("new" | "modified" | "deleted" | "unchanged")
result.diff_score   -> float (0.0 = identical, 1.0 = completely different)
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class DiffResult:
    asset_id:    int
    asset_type:  str               # "art" | "gump"
    change_type: str               # "new" | "modified" | "deleted" | "unchanged"
    diff_score:  float = 0.0       # 0.0 = identical, 1.0 = totally different
    details:     dict  = field(default_factory=dict)

    @property
    def is_changed(self) -> bool:
        return self.change_type != "unchanged"

    def __repr__(self) -> str:
        return (
            f"DiffResult(id={self.asset_id}, type={self.asset_type!r}, "
            f"change={self.change_type!r}, score={self.diff_score:.3f})"
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _pixel_diff_score(bytes_a: bytes, bytes_b: bytes) -> float:
    """
    Fast per-byte difference ratio.  Works on raw pixel data.
    Returns 0.0 for identical, 1.0 for completely different.
    """
    if not bytes_a and not bytes_b:
        return 0.0
    if not bytes_a or not bytes_b:
        return 1.0
    # Align lengths to the shorter one for a quick ratio
    length = max(len(bytes_a), len(bytes_b))
    short  = min(len(bytes_a), len(bytes_b))
    diffs  = sum(1 for a, b in zip(bytes_a, bytes_b) if a != b)
    # Treat any length difference as all-different for the excess bytes
    diffs += length - short
    return diffs / length


# ---------------------------------------------------------------------------
# DiffEngine
# ---------------------------------------------------------------------------

class DiffEngine:
    """
    Compares mod asset bytes against the clean client's bytes.

    Parameters
    ----------
    client_path : Path | str
        Path to the vanilla UO client directory (used to lazy-load readers).
    threshold : float
        Minimum diff_score to classify an asset as 'modified' (default: 0.0).
        At 0.0, *any* byte-level change counts.  Raise it to ignore minor
        compression artefacts or colour quantisation noise.
    """

    def __init__(self, client_path, threshold: float = 0.0) -> None:
        self._path      = Path(client_path)
        self._threshold = threshold
        self._art_reader   = None
        self._gump_reader  = None

    # ---- lazy reader access ------------------------------------------------

    def _get_art_reader(self):
        if self._art_reader is None:
            from .art_reader import ArtReader
            self._art_reader = ArtReader(self._path)
        return self._art_reader

    def _get_gump_reader(self):
        if self._gump_reader is None:
            from .gump_reader import GumpReader
            self._gump_reader = GumpReader(self._path)
        return self._gump_reader

    # ---- public API --------------------------------------------------------

    def diff_asset(
        self,
        asset_id:    int,
        asset_type:  str,
        clean_bytes: Optional[bytes],
        modded_bytes: Optional[bytes],
    ) -> DiffResult:
        """
        Compare clean bytes (from the vanilla client) against modded bytes.

        Parameters
        ----------
        asset_id    : numeric tile / gump ID
        asset_type  : "art" or "gump"
        clean_bytes : raw bytes from the vanilla client (None = asset missing)
        modded_bytes: raw bytes from the mod source    (None = asset missing)

        Returns a DiffResult with change_type and diff_score populated.
        """
        # ------------------------------------------------------------------
        # Classify by presence
        # ------------------------------------------------------------------
        if clean_bytes is None and modded_bytes is None:
            return DiffResult(asset_id, asset_type, "unchanged", 0.0)

        if clean_bytes is None:
            return DiffResult(asset_id, asset_type, "new", 1.0,
                              {"modded_size": len(modded_bytes)})

        if modded_bytes is None:
            return DiffResult(asset_id, asset_type, "deleted", 1.0,
                              {"clean_size": len(clean_bytes)})

        # ------------------------------------------------------------------
        # Fast-path: identical hash
        # ------------------------------------------------------------------
        if _sha256(clean_bytes) == _sha256(modded_bytes):
            return DiffResult(asset_id, asset_type, "unchanged", 0.0)

        # ------------------------------------------------------------------
        # Compute diff score
        # ------------------------------------------------------------------
        score = _pixel_diff_score(clean_bytes, modded_bytes)

        if score <= self._threshold:
            return DiffResult(asset_id, asset_type, "unchanged", score)

        return DiffResult(
            asset_id, asset_type, "modified", score,
            {
                "clean_size":  len(clean_bytes),
                "modded_size": len(modded_bytes),
                "score":       round(score, 4),
            },
        )

    def diff_art(
        self,
        asset_id:     int,
        modded_bytes: Optional[bytes],
    ) -> DiffResult:
        """
        Convenience wrapper - reads the clean bytes from the vanilla client
        automatically for the given art tile ID.
        """
        reader  = self._get_art_reader()
        raw     = reader._reader.read_raw(asset_id)
        return self.diff_asset(asset_id, "art", raw, modded_bytes)

    def diff_gump(
        self,
        asset_id:     int,
        modded_bytes: Optional[bytes],
    ) -> DiffResult:
        """
        Convenience wrapper - reads the clean bytes from the vanilla client
        automatically for the given gump ID.
        """
        reader = self._get_gump_reader()
        entry  = reader._reader.read_entry(asset_id)
        raw    = entry[0] if entry else None
        return self.diff_asset(asset_id, "gump", raw, modded_bytes)
