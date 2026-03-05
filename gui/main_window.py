# gui/main_window.py
# Main application window for UO Asset Toolkit.
# Layout: Asset Browser (left) | Preview + Diff Viewer (right) | Toolbar (top)

import os
import yaml
from typing import Optional
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QSplitter, QToolBar, QStatusBar, QMessageBox, QFileDialog
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt, QSettings, QSize
from PyQt6.QtWidgets import QApplication

from .asset_browser import AssetBrowserWidget
from .diff_viewer import DiffViewerWidget
from .preview_widget import PreviewLabel


CONFIG_PATH = "config.yaml"


class MainWindow(QMainWindow):
    """
    Root window. Owns the toolbar, status bar, and all panels.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("UO Asset Toolkit v5")
        self.setMinimumSize(1100, 700)
        self._config = self._load_config()
        self._setup_ui()
        self._restore_geometry()

    def _load_config(self) -> dict:
        if os.path.isfile(CONFIG_PATH):
            with open(CONFIG_PATH, "r") as f:
                return yaml.safe_load(f) or {}
        return {}

    def _setup_ui(self):
        # Toolbar
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(20, 20))
        self.addToolBar(toolbar)

        scan_action = QAction("Scan Assets", self)
        scan_action.setStatusTip("Scan all assets from the configured client")
        scan_action.triggered.connect(self._on_scan)
        toolbar.addAction(scan_action)

        diff_action = QAction("Show Diff", self)
        diff_action.setStatusTip("Compare clean vs modded client")
        diff_action.triggered.connect(self._on_diff)
        toolbar.addAction(diff_action)

        toolbar.addSeparator()

        modpack_action = QAction("Build Mod Pack", self)
        modpack_action.setStatusTip("Export modified assets to output/modpack/")
        modpack_action.triggered.connect(self._on_build_modpack)
        toolbar.addAction(modpack_action)

        # Status bar
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("Ready")

        # Central widget: splitter with browser on left, content on right
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: asset browser
        self._browser = AssetBrowserWidget(on_select=self._on_asset_selected)
        self._browser.setMinimumWidth(200)
        self._browser.setMaximumWidth(300)
        splitter.addWidget(self._browser)

        # Right: tabbed view (preview + diff viewer)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self._preview = PreviewLabel()
        self._diff_viewer = DiffViewerWidget()

        right_splitter = QSplitter(Qt.Orientation.Vertical)
        right_splitter.addWidget(self._preview)
        right_splitter.addWidget(self._diff_viewer)
        right_splitter.setSizes([300, 400])

        right_layout.addWidget(right_splitter)
        splitter.addWidget(right_panel)
        splitter.setSizes([250, 850])

        self.setCentralWidget(splitter)

        # Apply dark theme
        self.setStyleSheet("""
            QMainWindow { background-color: #0d0d1a; }
            QToolBar { background: #13132a; border-bottom: 1px solid #333; }
            QStatusBar { background: #0d0d1a; color: #888; }
            QSplitter::handle { background: #222; }
        """)

    def _on_asset_selected(self, asset_id: int):
        """Called when user selects an asset in the browser."""
        self.status.showMessage(f"Loading 0x{asset_id:04X}...")
        try:
            from formats.art import read_art_item
            client_path = self._config.get("client", {}).get("modded_path", "")
            img = read_art_item(client_path, asset_id)
            self._preview.set_image(img)
            self.status.showMessage(f"Asset 0x{asset_id:04X} loaded")
        except Exception as e:
            self.status.showMessage(f"Error: {e}")

    def _on_scan(self):
        self.status.showMessage("Scanning assets...")
        try:
            from commands.scan_art import scan_art
            scan_art()
            self.status.showMessage("Scan complete")
        except Exception as e:
            QMessageBox.warning(self, "Scan Error", str(e))

    def _on_diff(self):
        self.status.showMessage("Running diff...")
        QMessageBox.information(self, "Diff", "Select an asset in the browser to show its diff.")

    def _on_build_modpack(self):
        self.status.showMessage("Building mod pack...")
        try:
            from commands.build_modpack import build_modpack
            build_modpack()
            self.status.showMessage("Mod pack built -> output/modpack/")
        except Exception as e:
            QMessageBox.warning(self, "Build Error", str(e))

    def _restore_geometry(self):
        settings = QSettings("NerdyGamers", "UOAssetToolkit")
        geometry = settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)

    def closeEvent(self, event):
        settings = QSettings("NerdyGamers", "UOAssetToolkit")
        settings.setValue("geometry", self.saveGeometry())
        super().closeEvent(event)
