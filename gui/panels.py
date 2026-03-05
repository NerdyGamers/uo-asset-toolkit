"""
gui/panels.py - Notebook panel modules for the main GUI window

Provides three tab panels:
  ArtBrowserPanel  - browse/preview art tiles
  GumpBrowserPanel - browse/preview gumps
  DiffPanel        - compare mod against vanilla, build mod-packs
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox
from pathlib import Path

# Placeholder stub classes - extend later with real functionality

class ArtBrowserPanel(tk.Frame):
    def __init__(self, parent, app) -> None:
        super().__init__(parent, bg="#1e1e2e")
        self.app = app
        tk.Label(self, text="Art Browser - Coming Soon", bg="#1e1e2e", fg="#cdd6f4",
                 font=("Arial", 14)).pack(pady=100)

    def on_client_changed(self, path: Path | None) -> None:
        pass

    def on_mod_changed(self, path: Path | None) -> None:
        pass


class GumpBrowserPanel(tk.Frame):
    def __init__(self, parent, app) -> None:
        super().__init__(parent, bg="#1e1e2e")
        self.app = app
        tk.Label(self, text="Gump Browser - Coming Soon", bg="#1e1e2e", fg="#cdd6f4",
                 font=("Arial", 14)).pack(pady=100)

    def on_client_changed(self, path: Path | None) -> None:
        pass

    def on_mod_changed(self, path: Path | None) -> None:
        pass


class DiffPanel(tk.Frame):
    def __init__(self, parent, app) -> None:
        super().__init__(parent, bg="#1e1e2e")
        self.app = app
        tk.Label(self, text="Diff / Compare - Coming Soon", bg="#1e1e2e", fg="#cdd6f4",
                 font=("Arial", 14)).pack(pady=100)

    def on_client_changed(self, path: Path | None) -> None:
        pass

    def on_mod_changed(self, path: Path | None) -> None:
        pass
