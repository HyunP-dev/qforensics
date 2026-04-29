from __future__ import annotations

import os
import platform
from io import BytesIO

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from qforensics.model import *
from qforensics.model.evidencemodel import *
from qforensics.type.tskwrapper import TSKBytesIO
from qforensics.widget import *
from qforensics.widget.container import DynamicContainer


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Qforensics : : Digital Forensics OSS")
        with open("styles/dark.qss") as f:
            self.setStyleSheet(f.read())

        self.setCorner(Qt.Corner.TopLeftCorner, Qt.DockWidgetArea.LeftDockWidgetArea)
        self.setCorner(Qt.Corner.BottomLeftCorner, Qt.DockWidgetArea.LeftDockWidgetArea)
        self.setCorner(Qt.Corner.TopRightCorner, Qt.DockWidgetArea.RightDockWidgetArea)
        self.setCorner(
            Qt.Corner.BottomRightCorner, Qt.DockWidgetArea.RightDockWidgetArea
        )

        self.addToolBar(toolbar := QToolBar())
        toolbar.setStyleSheet("border: none;")
        
        toolbar.setIconSize(QSize(16, 16))
        attachAction = QAction("증거 이미지 탑재", self)

        attachAction.setIcon(QIcon("images/icons/drive--plus.png"))
        attachAction.triggered.connect(self.load)

        toolbar.addAction(attachAction)

        self.menuBar().addMenu(filemenu := QMenu("파일"))
        self.menuBar().addMenu(viewmenu := QMenu("보기"))
        self.menuBar().addMenu(helpmenu := QMenu("도움말"))
        self.menuBar().setStyleSheet("border: none; padding: 3px;")

        filemenu.addAction(attachAction)

        self.evidenceTree = QTreeView()
        self.evidenceTree.setModel(EvidenceTreeModel())
        self.evidenceTree.setHeaderHidden(True)
        self.evidenceTree.doubleClicked.connect(self.evidenceTreeDoubleClicked)
        self.evidenceTree.setEditTriggers(QTreeView.EditTrigger.NoEditTriggers)

        evidenceTreeDock = QDockWidget("탐색 트리", self)
        evidenceTreeDock.setWidget(self.evidenceTree)

        filesView = QTreeView()
        filesView.header().setSectionsClickable(True)

        self.filesView = filesView
        filesView.setEditTriggers(QTreeView.EditTrigger.NoEditTriggers)
        filesView.setRootIsDecorated(False)
        filesView.doubleClicked.connect(self.filesViewDoubleClicked)
        filesView.setModel(TSKFileBrowserModel())

        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, evidenceTreeDock)

        explorerRightDock = QDockWidget("파일 목록", self)
        explorerRightDock.setWidget(self.filesView)
        self.addDockWidget(Qt.DockWidgetArea.TopDockWidgetArea, explorerRightDock)

        viewerTabs = QTabWidget()
        self.hexview = HexViewer()
        viewerTabs.addTab(self.hexview, "Hex")
        self.textview = TextViewer()
        viewerTabs.addTab(self.textview, "문자열")
        self.viewerTabs = viewerTabs
        self.preview = DynamicContainer()
        viewerTabs.addTab(self.preview, "미리보기")

        self.propsView = QTreeView()
        propsDock = QDockWidget("속성", self)
        propsDock.setWidget(self.propsView)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, propsDock)
        self.resizeDocks(
            [evidenceTreeDock, propsDock], [70, 40], Qt.Orientation.Vertical
        )

        self.setDockNestingEnabled(True)
        self.resizeDocks(
            [evidenceTreeDock, explorerRightDock], [250, 750], Qt.Orientation.Horizontal
        )
        self.resizeDocks([explorerRightDock], [300], Qt.Orientation.Vertical)
        self.setCentralWidget(self.viewerTabs)
        self.setStatusBar(QStatusBar(self))

        self.resize(1000, 600)

    def showFiles(self, directory):
        model = TSKFileBrowserModel()
        model.open_dir(directory)
        self.filesView.setModel(model)

    @Slot(QModelIndex)
    def evidenceTreeDoubleClicked(self, index: QModelIndex):
        directory = None
        match item := index.internalPointer():
            case DirectoryItem():
                directory = item.entry.as_directory()
            case VolumeItem():
                if item.root_directory is None:
                    return
                directory = item.root_directory
        if directory is None:
            return
        self.showFiles(directory)

    @Slot(QModelIndex)
    def filesViewDoubleClicked(self, index: QModelIndex):
        entry = index.data(Qt.ItemDataRole.UserRole)

        if not isinstance(entry, pytsk3.File):
            return

        self.preview.replace_widget(QWidget())

        propsModel = QStandardItemModel()
        propsModel.setHorizontalHeaderLabels(["속성", "값"])
        propsModel.appendRow(
            [QStandardItem("파일명"), QStandardItem(entry.info.name.name.decode())]
        )
        propsModel.appendRow(
            [
                QStandardItem("파일 타입"),
                QStandardItem(
                    TSKFileBrowserModel.fstype_to_string(entry.info.meta.type)
                ),
            ]
        )
        
        self.propsView.setModel(propsModel)

        if entry.info.meta.type == pytsk3.TSK_FS_META_TYPE_REG:
            stream = TSKBytesIO(entry)

            def is_jpg(stream: TSKBytesIO) -> bool:
                offset = stream.tell()
                stream.seek(0)

                result = False
                if stream.read(4) == b"\xff\xd8\xff\xe1":
                    result = True

                stream.seek(offset)
                return result

            if is_jpg(stream):
                viewer = PhotoViewer(parent=self)
                viewer.open(stream.read())
                self.preview.replace_widget(viewer)

            def is_prefetch(stream: TSKBytesIO) -> bool:
                offset = stream.tell()
                stream.seek(4)
                if stream.read(4) == b"SCCA":
                    stream.seek(offset)
                    return True

                stream.seek(0)
                if stream.read(4) == b"MAM\x04":
                    stream.seek(offset)
                    return True

                stream.seek(offset)
                return False

            def is_regf(stream: TSKBytesIO) -> bool:
                offset = stream.tell()
                stream.seek(0)
                if stream.read(4) == b"regf":
                    stream.seek(offset)
                    return True

                stream.seek(offset)
                return False

            if is_regf(stream):
                viewer = HiveViewer()
                self.preview.replace_widget(viewer)
                viewer.parse(TSKBytesIO(entry))

            if is_prefetch(stream):
                viewer = SCCAViewer()
                self.preview.replace_widget(viewer)
                viewer.parse(TSKBytesIO(entry))

            if entry.info.meta.size > 0:
                self.hexview.upload(TSKBytesIO(entry))
                self.textview.upload(TSKBytesIO(entry))
            else:
                self.hexview.upload(BytesIO())
                self.textview.upload(BytesIO())

            self.hexview.show(1)
            self.textview.show(1)

    @Slot()
    def load(self):
        dialog = QFileDialog(self)
        path, _ = dialog.getOpenFileName()
        if not path:
            return
        if platform.system() == "Windows":
            path = path.replace("/", "\\")
        if isinstance(model := self.evidenceTree.model(), EvidenceTreeModel):
            model.upload(path)
