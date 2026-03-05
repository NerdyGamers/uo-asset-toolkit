# toolkit/uop_unpacker.py
# Reads assets from Ultima Online .uop container files.
# UOP format used by modern clients (e.g. artLegacyMUL.uop)

import os
import struct
import zlib
from typing import Dict, Optional


UOP_MAGIC = 0x50594D
UOP_VERSION = 5


class UOPEntry:
    __slots__ = ("offset", "header_length", "compressed_length", "decompressed_length",
                 "hash", "data_hash", "flag")

    def __init__(self, offset, header_length, compressed_length,
                 decompressed_length, hash_val, data_hash, flag):
        self.offset = offset
        self.header_length = header_length
        self.compressed_length = compressed_length
        self.decompressed_length = decompressed_length
        self.hash = hash_val
        self.data_hash = data_hash
        self.flag = flag


class UOPUnpacker:
    """
    Parses a .uop file and provides random access to individual entries by hash.
    """

    def __init__(self, uop_path: str):
        self.path = uop_path
        self._entries: Dict[int, UOPEntry] = {}
        self._load()

    def _load(self):
        with open(self.path, "rb") as f:
            magic, version, _, block_offset, _, count = struct.unpack("<IIIqII", f.read(28))
            if magic != UOP_MAGIC:
                raise ValueError(f"Not a valid UOP file: {self.path}")

            offset = block_offset
            while offset != 0:
                f.seek(offset)
                num_files, next_block = struct.unpack("<Iq", f.read(12))
                for _ in range(num_files):
                    (entry_offset, header_len, comp_len, decomp_len,
                     hash_val, data_hash, flag) = struct.unpack("<qiiiIIh", f.read(34))
                    if entry_offset == 0:
                        continue
                    entry = UOPEntry(entry_offset, header_len, comp_len,
                                     decomp_len, hash_val, data_hash, flag)
                    self._entries[hash_val] = entry
                offset = next_block

    def get_by_hash(self, hash_val: int) -> Optional[bytes]:
        entry = self._entries.get(hash_val)
        if entry is None:
            return None
        with open(self.path, "rb") as f:
            f.seek(entry.offset + entry.header_length)
            data = f.read(entry.compressed_length)
        if entry.flag == 1:
            data = zlib.decompress(data)
        return data

    @staticmethod
    def hash_filename(filename: str) -> int:
        """Compute UOP hash for a filename string."""
        eax = ecx = edx = ebx = esi = edi = 0
        filename = filename.upper()
        ptr = 0xDEADBEEF + len(filename)
        for ch in filename:
            val = ord(ch)
            ptr ^= val
            ptr &= 0xFFFFFFFF
        return ptr

    def entry_count(self) -> int:
        return len(self._entries)
