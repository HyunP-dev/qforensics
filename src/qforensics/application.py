from __future__ import annotations

from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

import signal
import platform

from .handler import *
from .window import MainWindow

signal.signal(signal.SIGINT, signal.SIG_DFL)


def run():
    app = QApplication()
    window = MainWindow()
    if platform.system() == "Windows":
        app.setStyle('Windows')
    if platform.system() == "Darwin":
        pass
    window.show()
    app.exec()
