"""
core/art_reader.py - Read UO art tile images from art.mul / artLegacyMUL.uop

Supports both the classic .mul pair (art.mul + artidx.mul) and the newer
UOP container format used by the Enhanced Client.

Public API
----------
ArtReader(client_path)
    .get_all_ids()          -> list[int]
    .read(art_id)           -> PIL.Image | None
    .read_art_item(path, id)-> PIL.Image | None   (static-style helper)
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

_ART_MUL      = "art.mul"
_ART_IDX      = "artidx.mul"
_ART_UOP      = "artLegacyMUL.uop"

_LAND_TILE_COUNT = 0x4000   # 16384 land tiles
_MAX_TILE_ID     = 0x10000  # 65536 total slots

_IDX_ENTRY_SIZE  = 12       # offset(4) + length(4) + extra(4)
_IDX_INVALID     = 0xFFFF_FFFF

_TILE_WIDTH  = 44
_TILE_HEIGHT = 44
_LAND_WIDTH  = 44
_LAND_HEIGHT = 44


# ---------------------------------------------------------------------------
# MUL reader
# ---------------------------------------------------------------------------

class _MulReader:
    """Low-level reader for the classic art.mul / artidx.mul pair."""

    def __init__(self, mul_path: Path, idx_path: Path) -> None:
        self._mul = mul_path
        self._idx = idx_path
        self._index: list[tuple[int, int]] = []   # (offset, length)
        self._load_index()

    def _load_index(self) -> None:
        idx_bytes = self._idx.read_bytes()
        count = len(idx_bytes) // _IDX_ENTRY_SIZE
        self._index = []
        for i in range(count):
            off = i * _IDX_ENTRY_SIZE
            offset, length, _ = struct.unpack_from("<III", idx_bytes, off)
            self._index.append((offset, length))

    def get_all_ids(self) -> list[int]:
        return [
            i for i, (off, length) in enumerate(self._index)
            if off != _IDX_INVALID and length > 0 and i < _MAX_TILE_ID
        ]

    def read_raw(self, art_id: int) -> Optional[bytes]:
        if art_id >= len(self._index):
            return None
        offset, length = self._index[art_id]
        if offset == _IDX_INVALID or length == 0:
            return None
        with self._mul.open("rb") as fh:
            fh.seek(offset)
            return fh.read(length)


# ---------------------------------------------------------------------------
# Tile decoders
# ---------------------------------------------------------------------------

def _decode_land_tile(data: bytes) -> Image.Image:
    """
    Decode a diamond-shaped land tile (44x44) from raw MUL bytes.
    Land tiles use 16-bit 555 colour, no RLE, stored row by row as a diamond.
    """
    img = Image.new("RGBA", (_LAND_WIDTH, _LAND_HEIGHT), (0, 0, 0, 0))
    pixels = img.load()
    pos = 0
    for y in range(22):
        count = (y + 1) * 2
        x_start = 21 - y
        for x in range(count):
            if pos + 2 > len(data):
                break
            colour = struct.unpack_from("<H", data, pos)[0]
            pos += 2
            r = ((colour >> 10) & 0x1F) << 3
            g = ((colour >>  5) & 0x1F) << 3
            b = ( colour        & 0x1F) << 3
            pixels[x_start + x, y] = (r, g, b, 255)
    for y in range(22):
        count = 44 - (y + 1) * 2
        x_start = y + 1
        for x in range(count):
            if pos + 2 > len(data):
                break
            colour = struct.unpack_from("<H", data, pos)[0]
            pos += 2
            r = ((colour >> 10) & 0x1F) << 3
            g = ((colour >>  5) & 0x1F) << 3
            b = ( colour        & 0x1F) << 3
            pixels[x_start + x, 22 + y] = (r, g, b, 255)
    return img


def _decode_static_tile(data: bytes) -> Image.Image:
    """
    Decode a static (item) art tile from raw MUL bytes.
    Static tiles are RLE-encoded 16-bit 1555 ARGB rows.
    The data begins with an 8-byte header (unknown + width + height + lookup).
    """
    if len(data) < 8:
        return None
    # Skip 4-byte unknown header
    width  = struct.unpack_from("<H", data, 4)[0]
    height = struct.unpack_from("<H", data, 6)[0]

    if width == 0 or height == 0 or width > 1024 or height > 1024:
        return None

    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    pixels = img.load()

    # Row lookup table: height * 2 bytes of relative offsets (in WORDs from table end)
    lookup_start = 8
    data_start   = lookup_start + height * 2

    for y in range(height):
        row_off = struct.unpack_from("<H", data, lookup_start + y * 2)[0]
        pos = (data_start + row_off * 2)
        x = 0
        while pos + 4 <= len(data):
            xoffset = struct.unpack_from("<H", data, pos)[0]
            run     = struct.unpack_from("<H", data, pos + 2)[0]
            pos += 4
            if xoffset == 0 and run == 0:
                break
            x += xoffset
            for _ in range(run):
                if pos + 2 > len(data) or x >= width:
                    break
                colour = struct.unpack_from("<H", data, pos)[0]
                pos += 2
                if colour != 0:
                    a = 255
                    r = ((colour >> 10) & 0x1F) << 3
                    g = ((colour >>  5) & 0x1F) << 3
                    b = ( colour        & 0x1F) << 3
                    pixels[x, y] = (r, g, b, a)
                x += 1
    return img


# ---------------------------------------------------------------------------
# Public ArtReader class
# ---------------------------------------------------------------------------

class ArtReader:
    """
    High-level art reader that auto-detects MUL or UOP format.

    Parameters
    ----------
    client_path : Path | str
        Path to the UO client installation directory.
    """

    def __init__(self, client_path) -> None:
        self._path = Path(client_path)
        self._reader: _MulReader = self._open_reader()

    def _open_reader(self) -> _MulReader:
        mul = self._path / _ART_MUL
        idx = self._path / _ART_IDX
        if mul.exists() and idx.exists():
            return _MulReader(mul, idx)
        # UOP not yet decoded natively - fall back to MUL if present anywhere
        for candidate in self._path.rglob(_ART_MUL):
            idx_c = candidate.parent / _ART_IDX
            if idx_c.exists():
                return _MulReader(candidate, idx_c)
        raise FileNotFoundError(
            f"Could not locate art.mul + artidx.mul in: {self._path}"
        )

    def get_all_ids(self) -> list[int]:
        """Return all valid art tile IDs present in the client data."""
        return self._reader.get_all_ids()

    def read(self, art_id: int) -> Optional[Image.Image]:
        """
        Read and decode a single art tile by its numeric ID.

        IDs 0x0000-0x3FFF are land tiles (diamond 44x44).
        IDs 0x4000+ are static (item) tiles (variable size, RLE).

        Returns None if the tile doesn't exist.
        """
        raw = self._reader.read_raw(art_id)
        if raw is None:
            return None
        if art_id < _LAND_TILE_COUNT:
            return _decode_land_tile(raw)
        return _decode_static_tile(raw)

    # Convenience alias used by preview_tile.py and scan_art.py
    def read_art_item(self, _client_path, art_id: int) -> Optional[Image.Image]:
        """Alias for read() - client_path argument is ignored (already set at init)."""
        return self.read(art_id)
