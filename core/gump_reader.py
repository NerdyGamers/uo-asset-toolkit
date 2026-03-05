"""
core/gump_reader.py - Read UO gump images from gumpart.mul / gumpidx.mul

Supports the classic .mul pair only (UOP support is a future extension).

Public API
----------
GumpReader(client_path)
    .get_all_ids()  -> list[int]
    .read(gump_id)  -> PIL.Image | None
"""

from __future__ import annotations

import struct
from pathlib import Path
from typing import Optional

try:
    from PIL import Image
except ImportError as exc:
    raise ImportError("Pillow is required: pip install Pillow") from exc


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_GUMP_MUL       = "gumpart.mul"
_GUMP_IDX       = "gumpidx.mul"
_IDX_ENTRY_SIZE = 12          # offset(4) + length(4) + extra(4)
_IDX_INVALID    = 0xFFFF_FFFF
_MAX_GUMP_ID    = 0x10000


# ---------------------------------------------------------------------------
# MUL reader
# ---------------------------------------------------------------------------

class _GumpMulReader:
    """Low-level reader for gumpart.mul / gumpidx.mul."""

    def __init__(self, mul_path: Path, idx_path: Path) -> None:
        self._mul = mul_path
        self._idx = idx_path
        self._index: list[tuple[int, int, int]] = []  # (offset, length, extra)
        self._load_index()

    def _load_index(self) -> None:
        idx_bytes = self._idx.read_bytes()
        count = len(idx_bytes) // _IDX_ENTRY_SIZE
        self._index = []
        for i in range(count):
            off = i * _IDX_ENTRY_SIZE
            offset, length, extra = struct.unpack_from("<III", idx_bytes, off)
            self._index.append((offset, length, extra))

    def get_all_ids(self) -> list[int]:
        return [
            i for i, (offset, length, _) in enumerate(self._index)
            if offset != _IDX_INVALID and length > 0 and i < _MAX_GUMP_ID
        ]

    def read_entry(self, gump_id: int) -> Optional[tuple[bytes, int, int]]:
        """
        Returns (raw_bytes, width, height) or None.
        The 'extra' field encodes width (high 16 bits) and height (low 16 bits).
        """
        if gump_id >= len(self._index):
            return None
        offset, length, extra = self._index[gump_id]
        if offset == _IDX_INVALID or length == 0:
            return None
        width  = (extra >> 16) & 0xFFFF
        height =  extra        & 0xFFFF
        with self._mul.open("rb") as fh:
            fh.seek(offset)
            raw = fh.read(length)
        return raw, width, height


# ---------------------------------------------------------------------------
# Gump decoder
# ---------------------------------------------------------------------------

def _decode_gump(raw: bytes, width: int, height: int) -> Optional[Image.Image]:
    """
    Decode a gump image from raw MUL bytes.

    Gumps are stored as RLE-compressed rows.  Each row starts with `height`
    DWORD offsets (relative to the start of the pixel data, in DWORDs).
    Each row is a sequence of (run_length, colour) DWORD pairs terminated
    by a zero run-length.
    """
    if width == 0 or height == 0 or width > 2048 or height > 2048:
        return None
    if len(raw) < height * 4:
        return None

    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    pixels = img.load()

    # Row lookup: height DWORDs giving the offset (in DWORDs) from the *start of the data*
    # where each row's RLE data begins.  The pixel data follows the lookup table.
    lookup = struct.unpack_from(f"<{height}I", raw, 0)

    for y in range(height):
        pos = lookup[y] * 4   # convert DWORD offset to byte offset
        x   = 0
        while pos + 4 <= len(raw):
            entry = struct.unpack_from("<I", raw, pos)[0]
            pos  += 4
            run    = (entry >> 16) & 0xFFFF
            colour =  entry        & 0xFFFF
            if run == 0:
                break
            # Colour is 16-bit 1555 ARGB - bit 15 is NOT alpha in gumps
            # (always opaque if colour != 0)
            r = ((colour >> 10) & 0x1F) << 3
            g = ((colour >>  5) & 0x1F) << 3
            b = ( colour        & 0x1F) << 3
            a = 0 if colour == 0 else 255
            for _ in range(run):
                if x >= width:
                    break
                pixels[x, y] = (r, g, b, a)
                x += 1

    return img


# ---------------------------------------------------------------------------
# Public GumpReader class
# ---------------------------------------------------------------------------

class GumpReader:
    """
    High-level gump reader.

    Parameters
    ----------
    client_path : Path | str
        Path to the UO client installation directory.
    """

    def __init__(self, client_path) -> None:
        self._path = Path(client_path)
        self._reader = self._open_reader()

    def _open_reader(self) -> _GumpMulReader:
        mul = self._path / _GUMP_MUL
        idx = self._path / _GUMP_IDX
        if mul.exists() and idx.exists():
            return _GumpMulReader(mul, idx)
        for candidate in self._path.rglob(_GUMP_MUL):
            idx_c = candidate.parent / _GUMP_IDX
            if idx_c.exists():
                return _GumpMulReader(candidate, idx_c)
        raise FileNotFoundError(
            f"Could not locate gumpart.mul + gumpidx.mul in: {self._path}"
        )

    def get_all_ids(self) -> list[int]:
        """Return all valid gump IDs present in the client data."""
        return self._reader.get_all_ids()

    def read(self, gump_id: int) -> Optional[Image.Image]:
        """
        Read and decode a single gump image by its numeric ID.
        Returns None if the gump doesn't exist or decoding fails.
        """
        entry = self._reader.read_entry(gump_id)
        if entry is None:
            return None
        raw, width, height = entry
        return _decode_gump(raw, width, height)
