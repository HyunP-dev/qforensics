from __future__ import annotations

from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from io import BytesIO
from math import ceil
import platform


class TextViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().addWidget(navigator := QWidget())
        navigator.setLayout(QHBoxLayout())
        navigator.layout().setContentsMargins(10, 10, 0, 0)
        navigator.layout().addWidget(QLabel("Page: "))
        pageSpinBox = QSpinBox()
        pageSpinBox.setMinimum(1)
        pageSpinBox.setMaximum(1)
        pageSpinBox.valueChanged.connect(self.pageSpinBoxValueChanged)
        self.pageSpinBox = pageSpinBox
        pageSpinBox.setFixedWidth(72)
        navigator.layout().addWidget(pageSpinBox)
        navigator.layout().addWidget(QLabel("/"))
        self.pages = QLabel("")
        navigator.layout().addWidget(self.pages)
        spacer = QSpacerItem(
            40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        navigator.layout().addItem(spacer)

        self.view = QPlainTextEdit()

        print(platform.system())
        if platform.system() == "Windows":
            self.view.setFont("consolas")
        if platform.system() == "Darwin":
            self.view.setFont("Andale Mono")

        self.view.setReadOnly(True)
        self.layout().addWidget(self.view)

        self.io = BytesIO()
        self.size = 0

    def upload(self, io: BytesIO):
        self.io = io
        self.io.seek(0, 2)
        self.size = self.io.tell()
        maximum = ceil(self.size/0x4000)
        self.pageSpinBox.setMaximum(maximum)
        self.pages.setText(str(maximum))

    def show(self, page: int):
        io = self.io
        io.seek(0x4000 * (page - 1))
        self.view.setPlainText(io.read(0x4000).decode("ascii", "replace"))

    def pageSpinBoxValueChanged(self):
        self.show(self.pageSpinBox.value())
