# formats/maps.py
# Reads UO map data from map0.mul etc.
# Each map cell is a MapCell: altitude (z) + tile ID.

import struct
import os
from typing import Optional, Tuple
from dataclasses import dataclass


MAP_CELL_SIZE = 3  # tile_id(2) + z(1)
BLOCK_SIZE = 196   # 4 header bytes + 64 cells * 3 bytes


@dataclass
class MapCell:
    tile_id: int
    z: int


@dataclass
class MapBlock:
    header: int
    cells: list  # 8x8 = 64 MapCell entries


def read_map_block(map_path: str, block_x: int, block_y: int, map_width: int = 896) -> Optional[MapBlock]:
    """
    Read a single 8x8 map block from map?.mul.
    map_width is in blocks (default Felucca/Trammel = 896 blocks wide).
    """
    if not os.path.isfile(map_path):
        return None

    block_index = block_y * map_width + block_x
    file_offset = block_index * BLOCK_SIZE

    with open(map_path, "rb") as f:
        f.seek(file_offset)
        raw = f.read(BLOCK_SIZE)

    if len(raw) < BLOCK_SIZE:
        return None

    header = struct.unpack_from("<I", raw, 0)[0]
    cells = []
    for i in range(64):
        cell_offset = 4 + i * MAP_CELL_SIZE
        tile_id = struct.unpack_from("<H", raw, cell_offset)[0]
        z = struct.unpack_from("<b", raw, cell_offset + 2)[0]
        cells.append(MapCell(tile_id=tile_id, z=z))

    return MapBlock(header=header, cells=cells)
