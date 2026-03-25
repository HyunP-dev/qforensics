from __future__ import annotations

import exif
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *


class PhotoViewer(QSplitter):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._embed = EmbedPhotoViewer(self)
        self._metaView = QTreeView(self)
        self._metaView.setRootIsDecorated(False)
        self._metaView.setEditTriggers(QTreeView.EditTrigger.NoEditTriggers)

        self.addWidget(self._metaView)
        self.addWidget(self._embed)
        self.setSizes([300, 900])

    def open(self, raw: bytes):
        self._embed.open(raw)
        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(["Key", "Value"])

        image = exif.Image(raw)
        for key, value in image.get_all().items():
            model.appendRow([QStandardItem(key), QStandardItem(str(value))])
        self._metaView.setModel(model)


class EmbedPhotoViewer(QLabel):
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
                Qt.TransformationMode.SmoothTransformation,
            )
            self.setPixmap(scaled)
