from __future__ import annotations

import datetime
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


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setStyleSheet("""
        QDockWidget::title {
            padding: 3px;
            border: 1px solid #a0a0a0;
            border-radius: 1px;
        }
        """)

        self.setCorner(Qt.TopLeftCorner, Qt.LeftDockWidgetArea)
        self.setCorner(Qt.BottomLeftCorner, Qt.LeftDockWidgetArea)

        self.addToolBar(toolbar := QToolBar())
        toolbar.setFloatable(False)
        toolbar.setMovable(False)
        toolbar.setFixedHeight(24)
        attachAction = QAction("이미지 탑재", self)
        attachAction.setIcon(
            QIcon(os.path.join(__file__, "..", "resources/icons/drive--plus.png"))
        )
        attachAction.triggered.connect(self.load)

        toolbar.addAction(attachAction)

        self.menuBar().addMenu(filemenu := QMenu("파일"))

        attachAction = QAction("이미지 탑재", self)
        attachAction.triggered.connect(self.load)
        filemenu.addAction(attachAction)

        self.evidenceTree = QTreeView()
        self.evidenceTree.setModel(EvidenceTreeModel())
        self.evidenceTree.setHeaderHidden(True)
        self.evidenceTree.doubleClicked.connect(self.evidenceTreeDoubleClicked)
        self.evidenceTree.setEditTriggers(QTreeView.EditTrigger.NoEditTriggers)

        evidenceTreeDock = QDockWidget("탐색 트리", self)
        # evidenceTreeDock.setLayout(QVBoxLayout())

        # evidenceTreeDock.layout().setContentsMargins(0, 0, 0, 0)
        evidenceTreeDock.setWidget(self.evidenceTree)

        self.resultTree = QTreeView()
        self.resultTree.setModel(ArtifactModel())
        self.resultTree.setHeaderHidden(True)
        self.resultTree.setEditTriggers(QTreeView.NoEditTriggers)
        self.resultTree.expandAll()
        self.resultTree.doubleClicked.connect(self.resultViewDoubleClicked)

        filesView = QTreeView()
        self.filesView = filesView
        filesView.setEditTriggers(QTreeView.NoEditTriggers)
        filesView.setRootIsDecorated(False)
        filesView.doubleClicked.connect(self.filesViewDoubleClicked)

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

        self.setDockNestingEnabled(True)
        self.resizeDocks(
            [evidenceTreeDock, explorerRightDock], [250, 750], Qt.Orientation.Horizontal
        )
        self.resizeDocks([explorerRightDock], [300], Qt.Vertical)
        self.setCentralWidget(self.viewerTabs)
        self.setStatusBar(QStatusBar(self))

        self.resize(1000, 600)

    @Slot(int)
    def leftTabBarClicked(self, index):
        print(index)

    def showFiles(self, *directories):
        model = TSKFileBrowserModel()
        model.open_dir(directories[0])
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
        self.viewerTabs.setCurrentIndex(0)

        if not isinstance(entry, pytsk3.File):
            return

        tabs_count = self.viewerTabs.count()
        if tabs_count > 2:
            for i in reversed(range(2, tabs_count)):
                self.viewerTabs.removeTab(i)

        if entry.info.meta.type == pytsk3.TSK_FS_META_TYPE_REG:
            stream = TSKBytesIO(entry)

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

            if is_prefetch(stream):
                viewer = SCCAViewer()
                self.viewerTabs.addTab(viewer, "분석 결과")
                viewer.parse(TSKBytesIO(entry))

            if entry.info.meta.size > 0:
                raw = entry.read_random(0, entry.info.meta.size)
                self.hexview.upload(TSKBytesIO(entry))
                self.textview.upload(TSKBytesIO(entry))

            else:
                self.hexview.upload(BytesIO())
                self.textview.upload(BytesIO())
            self.hexview.show(1)
            self.textview.show(1)

    @Slot(QModelIndex)
    def resultViewDoubleClicked(self, index: QModelIndex):
        match index.data(Qt.ItemDataRole.DisplayRole):
            case "프로그램 실행 기록":
                model = self.evidenceTree.model()
                model: EvidenceTreeModel
                directories = []
                for image_item in model.root_item.children:
                    match image_item:
                        case EWFImageItem():
                            for fs in image_item.filesystems:
                                try:
                                    directory = fs.open_dir("/Windows/Prefetch", 2)
                                    directories.append(directory)

                                except:
                                    continue
                self.showFiles(*directories)

    @Slot()
    def load(self):
        dialog = QFileDialog(self)
        path, _ = dialog.getOpenFileName()
        if not path:
            return
        if platform.system() == "Windows":
            path = path.replace("/", "\\")
        self.evidenceTree.model().upload(path)
