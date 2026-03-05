# gui/preview_widget.py
# Shared PIL Image -> QPixmap converter.
# Handles RGBA transparency correctly for sprite previews.

from typing import Optional
from PIL import Image
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel


def pil_to_pixmap(img: Image.Image, max_size: int = 256) -> QPixmap:
    """
    Convert a PIL Image to a QPixmap.
    Scales up small sprites using nearest-neighbor for pixel-accurate preview.
    Max dimension is capped at max_size pixels.
    """
    if img.mode != "RGBA":
        img = img.convert("RGBA")

    # Scale up tiny sprites so they're actually visible
    w, h = img.size
    if w < max_size and h < max_size:
        scale = min(max_size // max(w, 1), max_size // max(h, 1))
        if scale > 1:
            img = img.resize((w * scale, h * scale), Image.NEAREST)

    data = img.tobytes("raw", "RGBA")
    qimg = QImage(data, img.width, img.height, QImage.Format.Format_RGBA8888)
    return QPixmap.fromImage(qimg)


class PreviewLabel(QLabel):
    """
    A QLabel subclass that displays a PIL Image centered on a dark background.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(256, 256)
        self.setStyleSheet("background-color: #1a1a2e; border: 1px solid #444;")
        self.setText("No preview")
        self._current_img: Optional[Image.Image] = None

    def set_image(self, img: Optional[Image.Image]):
        """Display a PIL Image. Pass None to reset to placeholder text."""
        self._current_img = img
        if img is None:
            self.setPixmap(QPixmap())
            self.setText("No preview")
        else:
            pixmap = pil_to_pixmap(img)
            self.setPixmap(pixmap)
            self.setText("")
