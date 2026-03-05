# formats/textures.py
# Reads UO texture data from texmaps.mul / texidx.mul

import struct
import os
from typing import Optional
from PIL import Image


TEX_IDX_ENTRY = 12


def read_texture(client_path: str, texture_id: int) -> Optional[Image.Image]:
    """
    Read a texture tile (64x64 or 128x128) and return a PIL Image.
    Textures are stored as raw 16-bit color pixels.
    """
    mul_path = os.path.join(client_path, "texmaps.mul")
    idx_path = os.path.join(client_path, "texidx.mul")

    if not os.path.isfile(idx_path) or not os.path.isfile(mul_path):
        return None

    with open(idx_path, "rb") as f:
        f.seek(texture_id * TEX_IDX_ENTRY)
        raw = f.read(TEX_IDX_ENTRY)
        if len(raw) < TEX_IDX_ENTRY:
            return None
        offset, length, extra = struct.unpack("<III", raw)

    if offset == 0xFFFFFFFF or length == 0:
        return None

    # Determine size: 128x128 if length >= 32768, else 64x64
    size = 128 if length >= 32768 else 64

    with open(mul_path, "rb") as f:
        f.seek(offset)
        data = f.read(length)

    img = Image.new("RGBA", (size, size), (0, 0, 0, 255))
    offset = 0
    for y in range(size):
        for x in range(size):
            if offset + 1 >= len(data):
                break
            color = struct.unpack_from("<H", data, offset)[0]
            offset += 2
            r = ((color >> 10) & 0x1F) << 3
            g = ((color >> 5) & 0x1F) << 3
            b = (color & 0x1F) << 3
            img.putpixel((x, y), (r, g, b, 255))

    return img
