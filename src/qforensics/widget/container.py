from __future__ import annotations

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *


class DynamicContainer(QWidget):
    def __init__(self):
        super().__init__()
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self.current_content = None

    def replace_widget(self, new_widget: QWidget):
        if self.current_content:
            self._layout.removeWidget(self.current_content)
            self.current_content.deleteLater()

        self.current_content = new_widget
        self._layout.addWidget(new_widget)
