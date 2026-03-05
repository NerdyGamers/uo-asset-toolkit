# formats/art.py
# Reads UO art assets (items and land tiles) from art.mul / artidx.mul
# or artLegacyMUL.uop depending on client type.

import struct
import os
from typing import Optional
from PIL import Image


ARTIDX_ENTRY = 12  # offset(4) + length(4) + extra(4)
ITEM_OFFSET = 0x4000  # Items start at 0x4000 in the art index


def _read_mul_entry(mul_path: str, idx_path: str, index: int) -> Optional[bytes]:
    """Read raw bytes for a given index from a MUL+IDX pair."""
    if not os.path.isfile(idx_path) or not os.path.isfile(mul_path):
        return None
    with open(idx_path, "rb") as idx_f:
        idx_f.seek(index * ARTIDX_ENTRY)
        raw = idx_f.read(ARTIDX_ENTRY)
        if len(raw) < ARTIDX_ENTRY:
            return None
        offset, length, _ = struct.unpack("<III", raw)
    if offset == 0xFFFFFFFF or length == 0:
        return None
    with open(mul_path, "rb") as mul_f:
        mul_f.seek(offset)
        return mul_f.read(length)


def read_art_land(client_path: str, tile_id: int) -> Optional[Image.Image]:
    """
    Read a land tile (IDs 0x0000 - 0x3FFF) and return a PIL Image.
    Land tiles are 44x44 isometric diamonds.
    """
    mul = os.path.join(client_path, "art.mul")
    idx = os.path.join(client_path, "artidx.mul")
    data = _read_mul_entry(mul, idx, tile_id)
    if data is None or len(data) < 4:
        return None
    # Land tiles: 44*44 / 2 * 2 bytes (16-bit color)
    pixels = []
    offset = 4  # skip unknown header
    for y in range(22):
        width = (y + 1) * 2
        row = []
        for x in range(width):
            if offset + 1 >= len(data):
                break
            color = struct.unpack_from("<H", data, offset)[0]
            offset += 2
            r = ((color >> 10) & 0x1F) << 3
            g = ((color >> 5) & 0x1F) << 3
            b = (color & 0x1F) << 3
            row.append((r, g, b, 255))
        pixels.append(row)
    for y in range(22):
        width = (22 - y) * 2
        row = []
        for x in range(width):
            if offset + 1 >= len(data):
                break
            color = struct.unpack_from("<H", data, offset)[0]
            offset += 2
            r = ((color >> 10) & 0x1F) << 3
            g = ((color >> 5) & 0x1F) << 3
            b = (color & 0x1F) << 3
            row.append((r, g, b, 255))
        pixels.append(row)
    img = Image.new("RGBA", (44, 44), (0, 0, 0, 0))
    row_idx = 0
    for y in range(22):
        x_off = 21 - y
        for x, px in enumerate(pixels[row_idx]):
            img.putpixel((x_off + x, y), px)
        row_idx += 1
    for y in range(22):
        x_off = y
        row = pixels[row_idx] if row_idx < len(pixels) else []
        for x, px in enumerate(row):
            img.putpixel((x_off + x, 22 + y), px)
        row_idx += 1
    return img


def read_art_item(client_path: str, item_id: int) -> Optional[Image.Image]:
    """
    Read an item sprite (IDs 0x4000+) and return a PIL Image.
    """
    mul = os.path.join(client_path, "art.mul")
    idx = os.path.join(client_path, "artidx.mul")
    data = _read_mul_entry(mul, idx, ITEM_OFFSET + item_id)
    if data is None or len(data) < 8:
        return None
    offset = 4  # skip flag
    width = struct.unpack_from("<H", data, offset)[0]
    height = struct.unpack_from("<H", data, offset + 2)[0]
    if width == 0 or height == 0 or width > 1024 or height > 1024:
        return None
    offset += 4
    lookup_table_size = height * 2
    lookup = [struct.unpack_from("<H", data, offset + i * 2)[0] for i in range(height)]
    data_offset = offset + lookup_table_size
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    for y in range(height):
        row_offset = data_offset + lookup[y] * 2
        x = 0
        while row_offset + 3 < len(data):
            x_offset = struct.unpack_from("<H", data, row_offset)[0]
            run_length = struct.unpack_from("<H", data, row_offset + 2)[0]
            row_offset += 4
            if x_offset == 0 and run_length == 0:
                break
            x += x_offset
            for i in range(run_length):
                if row_offset + 1 >= len(data):
                    break
                color = struct.unpack_from("<H", data, row_offset)[0]
                row_offset += 2
                if color == 0:
                    x += 1
                    continue
                r = ((color >> 10) & 0x1F) << 3
                g = ((color >> 5) & 0x1F) << 3
                b = (color & 0x1F) << 3
                if 0 <= x < width and 0 <= y < height:
                    img.putpixel((x, y), (r, g, b, 255))
                x += 1
    return img
