# toolkit/hashing.py
# Fast asset hashing for diff detection.

import hashlib
import os
from typing import Optional


def hash_bytes(data: bytes, algorithm: str = "sha256") -> str:
    """Hash raw bytes and return hex digest."""
    h = hashlib.new(algorithm)
    h.update(data)
    return h.hexdigest()


def hash_file(path: str, algorithm: str = "sha256", chunk_size: int = 65536) -> Optional[str]:
    """Hash a file on disk in chunks. Returns None if file doesn't exist."""
    if not os.path.isfile(path):
        return None
    h = hashlib.new(algorithm)
    with open(path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def hash_asset(data: Optional[bytes], algorithm: str = "sha256") -> Optional[str]:
    """Hash an asset's raw bytes. Returns None if data is None."""
    if data is None:
        return None
    return hash_bytes(data, algorithm)


def assets_differ(hash_a: Optional[str], hash_b: Optional[str]) -> bool:
    """
    Returns True if two asset hashes differ.
    Treats (None, None) as identical and (None, value) as different.
    """
    return hash_a != hash_b
