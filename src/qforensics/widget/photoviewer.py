from __future__ import annotations

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *


class PhotoViewer(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self._pixmap = QPixmap()
        self.setAlignment(Qt.AlignCenter)
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
    
    def open(self, raw: bytes):
        if not self._pixmap.loadFromData(raw):
            return
        self._update_pixmap()

    def resizeEvent(self, event: QResizeEvent):
        self._update_pixmap()
        super().resizeEvent(event)

    def _update_pixmap(self):
        if not self._pixmap.isNull():
            scaled = self._pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            self.setPixmap(scaled)
