# gui/diff_viewer.py
# Side-by-side sprite diff viewer.
# Clean client on the left, modded client on the right, pixel diff overlay below.

from typing import Optional
from PIL import Image, ImageChops
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt
from .preview_widget import PreviewLabel, pil_to_pixmap


class DiffViewerWidget(QWidget):
    """
    Three-panel diff viewer:
      Left:   Clean client sprite
      Center: Pixel diff overlay (red-channel amplified)
      Right:  Modded client sprite
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)

        title = QLabel("Diff Viewer")
        title.setStyleSheet("font-weight: bold; font-size: 13px; color: #ccc;")
        main_layout.addWidget(title)

        self._id_label = QLabel("Select an asset to compare")
        self._id_label.setStyleSheet("color: #aaa; font-family: monospace;")
        main_layout.addWidget(self._id_label)

        panels = QHBoxLayout()

        self._clean_panel = self._make_panel("Clean Client")
        self._diff_panel = self._make_panel("Pixel Diff")
        self._modded_panel = self._make_panel("Modded Client")

        panels.addWidget(self._clean_panel["frame"])
        panels.addWidget(self._diff_panel["frame"])
        panels.addWidget(self._modded_panel["frame"])
        main_layout.addLayout(panels)

    def _make_panel(self, title: str) -> dict:
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        frame.setStyleSheet("background: #0d0d1a; border: 1px solid #333;")
        layout = QVBoxLayout(frame)

        label = QLabel(title)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(label)

        preview = PreviewLabel()
        preview.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(preview)

        return {"frame": frame, "preview": preview, "label": label}

    def set_diff(
        self,
        asset_id: int,
        clean_img: Optional[Image.Image],
        modded_img: Optional[Image.Image],
    ):
        """Display a side-by-side diff for the given asset ID."""
        self._id_label.setText(f"Asset ID: 0x{asset_id:04X}")
        self._clean_panel["preview"].set_image(clean_img)
        self._modded_panel["preview"].set_image(modded_img)

        # Compute pixel diff overlay
        diff_img = self._compute_diff(clean_img, modded_img)
        self._diff_panel["preview"].set_image(diff_img)

    def _compute_diff(
        self,
        img_a: Optional[Image.Image],
        img_b: Optional[Image.Image],
    ) -> Optional[Image.Image]:
        """Generate a red-channel-amplified pixel diff between two images."""
        if img_a is None or img_b is None:
            return None

        # Resize to same dimensions for comparison
        size = (max(img_a.width, img_b.width), max(img_a.height, img_b.height))
        a = img_a.convert("RGBA").resize(size, Image.NEAREST)
        b = img_b.convert("RGBA").resize(size, Image.NEAREST)

        diff = ImageChops.difference(a, b)
        r, g, blue, alpha = diff.split()

        # Amplify red channel to make diffs visible
        from PIL import ImageEnhance
        r_enhanced = ImageEnhance.Brightness(r).enhance(5.0)
        return Image.merge("RGBA", (r_enhanced, g, blue, Image.new("L", size, 200)))
