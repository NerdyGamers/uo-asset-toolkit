"""
gui/app.py - Main application window for UO Asset Toolkit v5

Launches a Tkinter-based GUI that lets artists:
  * Browse and preview art tiles and gumps side-by-side
  * Load a mod folder and compare it against a vanilla client
  * Export changed assets or build a full mod-pack

Run directly:
    python -m uo_asset_toolkit gui
    python gui/app.py

Requires: Pillow, tkinter (standard library)
"""

from __future__ import annotations

import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path

try:
    from PIL import Image, ImageTk
except ImportError:
    print("[gui] ERROR: Pillow not installed.  Run: pip install Pillow", file=sys.stderr)
    sys.exit(1)

from .panels       import ArtBrowserPanel, GumpBrowserPanel, DiffPanel
from .preview_widget import PreviewWidget


# ---------------------------------------------------------------------------
# Application constants
# ---------------------------------------------------------------------------

APP_TITLE   = "UO Asset Toolkit v5"
WIN_WIDTH   = 1280
WIN_HEIGHT  = 800
MIN_WIDTH   = 900
MIN_HEIGHT  = 600

_ACCENT     = "#1e90ff"
_BG         = "#1e1e2e"
_FG         = "#cdd6f4"
_PANEL_BG   = "#181825"


# ---------------------------------------------------------------------------
# Main Application window
# ---------------------------------------------------------------------------

class App(tk.Tk):
    """
    Top-level application window.
    Hosts a notebook with Art Browser, Gump Browser and Diff panels.
    """

    def __init__(self) -> None:
        super().__init__()
        self.title(APP_TITLE)
        self.geometry(f"{WIN_WIDTH}x{WIN_HEIGHT}")
        self.minsize(MIN_WIDTH, MIN_HEIGHT)
        self.configure(bg=_BG)

        self._client_path: Path | None = None
        self._mod_path:    Path | None = None

        self._build_menu()
        self._build_toolbar()
        self._build_notebook()
        self._build_statusbar()

    # ---- Menu --------------------------------------------------------------

    def _build_menu(self) -> None:
        menu = tk.Menu(self, tearoff=False, bg=_PANEL_BG, fg=_FG,
                       activebackground=_ACCENT, activeforeground="white")

        file_menu = tk.Menu(menu, tearoff=False, bg=_PANEL_BG, fg=_FG,
                            activebackground=_ACCENT, activeforeground="white")
        file_menu.add_command(label="Open Client Folder...", command=self._open_client)
        file_menu.add_command(label="Open Mod Folder...",   command=self._open_mod)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        menu.add_cascade(label="File", menu=file_menu)

        tools_menu = tk.Menu(menu, tearoff=False, bg=_PANEL_BG, fg=_FG,
                             activebackground=_ACCENT, activeforeground="white")
        tools_menu.add_command(label="Scan Art...",    command=self._run_scan_art)
        tools_menu.add_command(label="Export Gumps...", command=self._run_export_gumps)
        tools_menu.add_command(label="Build Mod-Pack...", command=self._run_build_modpack)
        menu.add_cascade(label="Tools", menu=tools_menu)

        help_menu = tk.Menu(menu, tearoff=False, bg=_PANEL_BG, fg=_FG,
                            activebackground=_ACCENT, activeforeground="white")
        help_menu.add_command(label="About", command=self._show_about)
        menu.add_cascade(label="Help", menu=help_menu)

        self.config(menu=menu)

    # ---- Toolbar -----------------------------------------------------------

    def _build_toolbar(self) -> None:
        bar = tk.Frame(self, bg=_PANEL_BG, height=36)
        bar.pack(side=tk.TOP, fill=tk.X)

        tk.Button(bar, text="Open Client", bg=_ACCENT, fg="white", relief=tk.FLAT,
                  padx=8, command=self._open_client).pack(side=tk.LEFT, padx=4, pady=4)
        tk.Button(bar, text="Open Mod",    bg=_PANEL_BG, fg=_FG, relief=tk.FLAT,
                  padx=8, command=self._open_mod).pack(side=tk.LEFT, padx=4, pady=4)

        self._client_lbl = tk.Label(bar, text="No client loaded", bg=_PANEL_BG, fg="#888")
        self._client_lbl.pack(side=tk.LEFT, padx=16)

        self._mod_lbl = tk.Label(bar, text="No mod loaded", bg=_PANEL_BG, fg="#888")
        self._mod_lbl.pack(side=tk.LEFT, padx=8)

    # ---- Notebook ----------------------------------------------------------

    def _build_notebook(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook",           background=_BG,       borderwidth=0)
        style.configure("TNotebook.Tab",       background=_PANEL_BG, foreground=_FG,
                        padding=[10, 4])
        style.map("TNotebook.Tab",             background=[("selected", _ACCENT)],
                                               foreground=[("selected", "white")])

        nb = ttk.Notebook(self)
        nb.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        self._art_panel  = ArtBrowserPanel(nb,  app=self)
        self._gump_panel = GumpBrowserPanel(nb, app=self)
        self._diff_panel = DiffPanel(nb,        app=self)

        nb.add(self._art_panel,  text="Art Browser")
        nb.add(self._gump_panel, text="Gump Browser")
        nb.add(self._diff_panel, text="Diff / Compare")

        self._notebook = nb

    # ---- Status bar --------------------------------------------------------

    def _build_statusbar(self) -> None:
        bar = tk.Frame(self, bg=_PANEL_BG, height=22)
        bar.pack(side=tk.BOTTOM, fill=tk.X)
        self._status = tk.Label(bar, text="Ready", bg=_PANEL_BG, fg="#888",
                                anchor=tk.W, padx=8)
        self._status.pack(side=tk.LEFT)

    # ---- Public helpers used by panels ------------------------------------

    def set_status(self, msg: str) -> None:
        self._status.config(text=msg)
        self.update_idletasks()

    @property
    def client_path(self) -> Path | None:
        return self._client_path

    @property
    def mod_path(self) -> Path | None:
        return self._mod_path

    # ---- File actions ------------------------------------------------------

    def _open_client(self) -> None:
        path = filedialog.askdirectory(title="Select UO Client Folder")
        if path:
            self._client_path = Path(path)
            self._client_lbl.config(text=f"Client: {self._client_path.name}", fg=_FG)
            self.set_status(f"Client loaded: {self._client_path}")
            self._notify_panels_client_changed()

    def _open_mod(self) -> None:
        path = filedialog.askdirectory(title="Select Mod Source Folder")
        if path:
            self._mod_path = Path(path)
            self._mod_lbl.config(text=f"Mod: {self._mod_path.name}", fg=_FG)
            self.set_status(f"Mod loaded: {self._mod_path}")
            self._notify_panels_mod_changed()

    def _notify_panels_client_changed(self) -> None:
        for panel in (self._art_panel, self._gump_panel, self._diff_panel):
            if hasattr(panel, "on_client_changed"):
                panel.on_client_changed(self._client_path)

    def _notify_panels_mod_changed(self) -> None:
        for panel in (self._art_panel, self._gump_panel, self._diff_panel):
            if hasattr(panel, "on_mod_changed"):
                panel.on_mod_changed(self._mod_path)

    # ---- Tool launchers (delegate to command modules) ----------------------

    def _run_scan_art(self) -> None:
        if not self._client_path:
            messagebox.showwarning("No Client", "Please open a client folder first.")
            return
        out = filedialog.askdirectory(title="Select Output Directory")
        if not out:
            return
        self.set_status("Scanning art tiles...")
        try:
            from commands.scan_art import run as scan_run
            import argparse
            args = argparse.Namespace(
                client=str(self._client_path),
                output=out,
                workers=4,
                format="png",
                skip_land=False,
                skip_static=False,
                verbose=False,
            )
            scan_run(args)
            self.set_status(f"Art scan complete -> {out}")
            messagebox.showinfo("Done", f"Art tiles exported to:\n{out}")
        except Exception as exc:
            messagebox.showerror("Error", str(exc))
            self.set_status("Art scan failed.")

    def _run_export_gumps(self) -> None:
        if not self._client_path:
            messagebox.showwarning("No Client", "Please open a client folder first.")
            return
        out = filedialog.askdirectory(title="Select Output Directory")
        if not out:
            return
        self.set_status("Exporting gumps...")
        try:
            from commands.export_gumps import run as eg_run
            import argparse
            args = argparse.Namespace(
                client=str(self._client_path),
                output=out,
                ids="",
                format="png",
                workers=4,
                no_alpha=False,
                verbose=False,
            )
            eg_run(args)
            self.set_status(f"Gump export complete -> {out}")
            messagebox.showinfo("Done", f"Gumps exported to:\n{out}")
        except Exception as exc:
            messagebox.showerror("Error", str(exc))
            self.set_status("Gump export failed.")

    def _run_build_modpack(self) -> None:
        messagebox.showinfo(
            "Build Mod-Pack",
            "Use the Diff / Compare tab to detect changes, then click\n"
            "'Build Mod-Pack' in that panel."
        )
        self._notebook.select(2)

    # ---- About dialog ------------------------------------------------------

    def _show_about(self) -> None:
        messagebox.showinfo(
            "About",
            f"{APP_TITLE}\n"
            "A visual modding suite for Ultima Online.\n\n"
            "Supports art.mul, artidx.mul, gumpart.mul, gumpidx.mul\n"
            "Outputs: PNG exports, mod-packs with manifest.json"
        )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
