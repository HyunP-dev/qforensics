from __future__ import annotations

from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

import signal

from .handler import *
from .window import MainWindow

signal.signal(signal.SIGINT, signal.SIG_DFL)


def run():
    app = QApplication()
    # print(QStyleFactory.keys())
    # app.setStyle('Windows')
    window = MainWindow()
    window.show()
    app.exec()
