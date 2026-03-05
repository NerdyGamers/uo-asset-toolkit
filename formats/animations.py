# formats/animations.py
# Reads UO animation frames from anim.mul / anim.idx
# Animations are organized as: body -> action -> direction -> frames

import struct
import os
from typing import Optional, List
from PIL import Image


ANIM_IDX_ENTRY = 12


class AnimFrame:
    def __init__(self, image: Image.Image, center_x: int, center_y: int):
        self.image = image
        self.center_x = center_x
        self.center_y = center_y


def _get_anim_index(body: int, action: int, direction: int, frame: int) -> int:
    """Compute the flat index into the anim index file."""
    return ((body * 110 + action) * 5 + direction) * 2 + frame


def read_anim_frame(
    client_path: str,
    body: int,
    action: int,
    direction: int,
    frame: int,
) -> Optional[AnimFrame]:
    """
    Read a single animation frame and return an AnimFrame.
    Returns None if the frame does not exist.
    """
    mul_path = os.path.join(client_path, "anim.mul")
    idx_path = os.path.join(client_path, "anim.idx")

    if not os.path.isfile(idx_path) or not os.path.isfile(mul_path):
        return None

    index = _get_anim_index(body, action, direction, frame)

    with open(idx_path, "rb") as f:
        f.seek(index * ANIM_IDX_ENTRY)
        raw = f.read(ANIM_IDX_ENTRY)
        if len(raw) < ANIM_IDX_ENTRY:
            return None
        offset, length, extra = struct.unpack("<III", raw)

    if offset == 0xFFFFFFFF or length == 0:
        return None

    with open(mul_path, "rb") as f:
        f.seek(offset)
        data = f.read(length)

    if len(data) < 8:
        return None

    # Read palette (256 * 2 bytes = 512 bytes)
    palette = []
    for i in range(256):
        color = struct.unpack_from("<H", data, i * 2)[0]
        r = ((color >> 10) & 0x1F) << 3
        g = ((color >> 5) & 0x1F) << 3
        b = (color & 0x1F) << 3
        palette.append((r, g, b, 255 if color != 0 else 0))

    offset = 512
    center_x = struct.unpack_from("<h", data, offset)[0]
    center_y = struct.unpack_from("<h", data, offset + 2)[0]
    width = struct.unpack_from("<H", data, offset + 4)[0]
    height = struct.unpack_from("<H", data, offset + 6)[0]
    offset += 8

    if width == 0 or height == 0 or width > 1024 or height > 1024:
        return None

    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    line_offsets = [struct.unpack_from("<I", data, offset + i * 4)[0] for i in range(height)]
    data_start = offset + height * 4

    for y in range(height):
        line_off = data_start + line_offsets[y]
        x = 0
        while line_off < len(data) - 3:
            header = struct.unpack_from("<I", data, line_off)[0]
            line_off += 4
            if header == 0x7FFF7FFF:
                break
            x_offset = (header >> 22) & 0x3FF
            run_length = (header >> 12) & 0x3FF
            palette_offset = header & 0xFFF
            x += x_offset
            for i in range(run_length):
                if line_off >= len(data):
                    break
                color_idx = (palette_offset + i) & 0xFF
                px = palette[color_idx]
                if px[3] > 0 and 0 <= x < width and 0 <= y < height:
                    img.putpixel((x, y), px)
                x += 1

    return AnimFrame(image=img, center_x=center_x, center_y=center_y)
