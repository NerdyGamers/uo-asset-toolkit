# gui/asset_browser.py
# Left-panel asset list widget.
# Populated from AssetRegistry (index-driven, no empty slot spam).

from typing import Callable, Optional, List
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QLineEdit, QLabel
from PyQt6.QtCore import Qt


class AssetBrowserWidget(QWidget):
    """
    Displays a filterable list of asset IDs.
    Calls on_select(asset_id) when the user clicks an item.
    """

    def __init__(self, on_select: Callable[[int], None], parent=None):
        super().__init__(parent)
        self.on_select = on_select
        self._all_ids: List[int] = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        header = QLabel("Asset Browser")
        header.setStyleSheet("font-weight: bold; font-size: 13px; color: #ccc;")
        layout.addWidget(header)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Filter by ID or hex...")
        self._search.textChanged.connect(self._filter)
        layout.addWidget(self._search)

        self._list = QListWidget()
        self._list.setStyleSheet("background: #111; color: #eee; font-family: monospace;")
        self._list.currentTextChanged.connect(self._on_item_changed)
        layout.addWidget(self._list)

        self._count_label = QLabel("0 assets")
        self._count_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(self._count_label)

    def load_ids(self, asset_ids: List[int]):
        """Populate the browser with a list of asset IDs."""
        self._all_ids = sorted(asset_ids)
        self._populate(self._all_ids)

    def _populate(self, ids: List[int]):
        self._list.clear()
        for asset_id in ids:
            item = QListWidgetItem(f"0x{asset_id:04X}")
            item.setData(Qt.ItemDataRole.UserRole, asset_id)
            self._list.addItem(item)
        self._count_label.setText(f"{len(ids)} assets")

    def _filter(self, text: str):
        text = text.strip().lower()
        if not text:
            self._populate(self._all_ids)
            return
        filtered = [
            i for i in self._all_ids
            if text in f"0x{i:04x}" or text in str(i)
        ]
        self._populate(filtered)

    def _on_item_changed(self, text: str):
        if not text:
            return
        try:
            asset_id = int(text, 16)
            self.on_select(asset_id)
        except ValueError:
            pass
