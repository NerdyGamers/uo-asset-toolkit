# formats/gumps.py
# Reads UO gump images from gumpart.mul / gumpidx.mul

import struct
import os
from typing import Optional
from PIL import Image


GUMP_IDX_ENTRY = 12


def read_gump(client_path: str, gump_id: int) -> Optional[Image.Image]:
    """
    Read a gump image and return a PIL Image.
    Gumps use RLE compression with 16-bit color.
    """
    mul_path = os.path.join(client_path, "gumpart.mul")
    idx_path = os.path.join(client_path, "gumpidx.mul")

    if not os.path.isfile(idx_path) or not os.path.isfile(mul_path):
        return None

    with open(idx_path, "rb") as f:
        f.seek(gump_id * GUMP_IDX_ENTRY)
        raw = f.read(GUMP_IDX_ENTRY)
        if len(raw) < GUMP_IDX_ENTRY:
            return None
        offset, length, extra = struct.unpack("<III", raw)

    if offset == 0xFFFFFFFF or length == 0:
        return None

    width = (extra >> 16) & 0xFFFF
    height = extra & 0xFFFF
    if width == 0 or height == 0 or width > 2048 or height > 2048:
        return None

    with open(mul_path, "rb") as f:
        f.seek(offset)
        data = f.read(length)

    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    line_offsets = [struct.unpack_from("<I", data, i * 4)[0] * 4 for i in range(height)]

    for y in range(height):
        line_offset = line_offsets[y]
        x = 0
        while line_offset + 3 < len(data):
            run = struct.unpack_from("<H", data, line_offset)[0]
            color = struct.unpack_from("<H", data, line_offset + 2)[0]
            line_offset += 4
            if run == 0 and color == 0:
                break
            for i in range(run):
                if color != 0 and x < width:
                    r = ((color >> 10) & 0x1F) << 3
                    g = ((color >> 5) & 0x1F) << 3
                    b = (color & 0x1F) << 3
                    img.putpixel((x, y), (r, g, b, 255))
                x += 1

    return img
