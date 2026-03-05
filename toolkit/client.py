# toolkit/client.py
# UOClient - unified interface for reading both clean and modded UO clients.

import os
import yaml


class UOClient:
    """
    Wraps a single Ultima Online client installation.
    Provides unified access to MUL and UOP asset containers.
    """

    def __init__(self, path: str):
        self.path = path
        self._validate_path()

    def _validate_path(self):
        if not os.path.isdir(self.path):
            raise FileNotFoundError(f"Client path not found: {self.path}")

    def get_file(self, filename: str) -> str:
        """Returns full path to a client file."""
        return os.path.join(self.path, filename)

    def has_file(self, filename: str) -> bool:
        """Returns True if the client contains the given file."""
        return os.path.isfile(self.get_file(filename))

    def is_uop(self) -> bool:
        """Detect whether this client uses UOP containers."""
        return self.has_file("artLegacyMUL.uop")

    def is_mul(self) -> bool:
        """Detect whether this client uses legacy MUL files."""
        return self.has_file("art.mul") and self.has_file("artidx.mul")

    def get_art_files(self):
        """Returns (art_data_path, art_index_path) tuple based on client type."""
        if self.is_uop():
            return self.get_file("artLegacyMUL.uop"), None
        elif self.is_mul():
            return self.get_file("art.mul"), self.get_file("artidx.mul")
        else:
            raise FileNotFoundError("No art data files found in client path.")

    def get_gump_files(self):
        """Returns (gump_data_path, gump_index_path) tuple."""
        if self.has_file("gumpartLegacyMUL.uop"):
            return self.get_file("gumpartLegacyMUL.uop"), None
        return self.get_file("gumpart.mul"), self.get_file("gumpidx.mul")

    def __repr__(self):
        mode = "UOP" if self.is_uop() else "MUL" if self.is_mul() else "Unknown"
        return f"<UOClient path={self.path!r} mode={mode}>"
