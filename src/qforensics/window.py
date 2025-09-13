from __future__ import annotations

from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from qforensics.model import EvidenceTreeModel
from qforensics.model.evidencemodel import *
from qforensics.widget import *

import datetime
from io import BytesIO
import platform


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.menuBar().addMenu(filemenu := QMenu("파일"))

        attachAction = QAction("이미지 탑재", self)
        attachAction.triggered.connect(self.load)
        filemenu.addAction(attachAction)

        self.evidenceTree = QTreeView()
        self.evidenceTree.setModel(EvidenceTreeModel())
        self.evidenceTree.setHeaderHidden(True)
        self.evidenceTree.doubleClicked.connect(self.evidenceTreeDoubleClicked)
        self.evidenceTree.setEditTriggers(QTreeView.NoEditTriggers)

        self.leftPanel = QWidget()
        self.leftPanel.setLayout(QVBoxLayout())
        self.leftPanel.layout().setContentsMargins(0, 0, 0, 0)
        self.leftTabs = QTabWidget()
        self.leftPanel.layout().addWidget(self.leftTabs)
        self.leftTabs.addTab(self.evidenceTree, "증거 트리")

        self.rightPanel = QWidget()
        self.rightPanel.setLayout(QVBoxLayout())
        self.rightPanel.layout().setContentsMargins(0, 0, 0, 0)
        self.rightTabs = QTabWidget()
        self.rightPanel.layout().addWidget(self.rightTabs)
        self.filesView = QTreeView()
        self.filesView.setEditTriggers(QTreeView.NoEditTriggers)
        self.filesView.setRootIsDecorated(False)
        self.rightTabs.addTab(self.filesView, "파일 목록")
        self.filesView.doubleClicked.connect(self.filesViewDoubleClicked)

        self.splitter = QSplitter()
        self.splitter.addWidget(self.leftPanel)

        rightSplitter = QSplitter()
        rightSplitter.setOrientation(Qt.Orientation.Vertical)
        rightSplitter.addWidget(self.rightPanel)

        viewerTabs = QTabWidget()
        self.hexview = HexViewer()
        viewerTabs.addTab(self.hexview, "Hex")
        self.textview = TextViewer()
        viewerTabs.addTab(self.textview, "문자열")
        rightSplitter.addWidget(viewerTabs)

        self.splitter.addWidget(rightSplitter)

        self.splitter.setStretchFactor(0, 3)
        self.splitter.setStretchFactor(1, 7)
        self.setCentralWidget(self.splitter)
        self.resize(1000, 600)

    @Slot(QModelIndex)
    def evidenceTreeDoubleClicked(self, index: QModelIndex):
        directory = None
        match (item := index.internalPointer()):
            case DirectoryItem():
                directory = item.entry.as_directory()
            case VolumeItem():
                if item.root_directory is None:
                    return
                directory = item.root_directory
        if directory is None:
            return
        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(["파일명", "크기", "타입", "변경 시간"])
        self.filesView.setModel(model)
        for entry in directory:
            if entry.info.name.name in [b".", b".."]:
                continue
            ftype = ""
            if entry.info.meta:
                if entry.info.meta.type == pytsk3.TSK_FS_NAME_TYPE_UNDEF:
                    ftype = "Unknown type"
                if entry.info.meta.type == pytsk3.TSK_FS_NAME_TYPE_FIFO:
                    ftype = "Named pipe"
                if entry.info.meta.type == pytsk3.TSK_FS_NAME_TYPE_CHR:
                    ftype = "Character device"
                if entry.info.meta.type == pytsk3.TSK_FS_META_TYPE_DIR:
                    ftype = "Directory"
                if entry.info.meta.type == pytsk3.TSK_FS_META_TYPE_BLK:
                    ftype = "Block device"
                if entry.info.meta.type == pytsk3.TSK_FS_META_TYPE_REG:
                    ftype = "Regular file"
                if entry.info.meta.type == pytsk3.TSK_FS_META_TYPE_LNK:
                    ftype = "Symbolic link"
                if entry.info.meta.type == pytsk3.TSK_FS_META_TYPE_SOCK:
                    ftype = "Socket"
                if entry.info.meta.type == pytsk3.TSK_FS_NAME_TYPE_SHAD:
                    ftype = "Shadow inode (solaris)"
                if entry.info.meta.type == pytsk3.TSK_FS_NAME_TYPE_WHT:
                    ftype = "Whiteout (openbsd)"
                if entry.info.meta.type == pytsk3.TSK_FS_NAME_TYPE_VIRT:
                    ftype = "Special (TSK added \"Virtual\" files)"
                if entry.info.meta.type == pytsk3.TSK_FS_NAME_TYPE_VIRT_DIR:
                    ftype = "Special (TSK added \"Virtual\" directories)"

            item = QStandardItem(entry.info.name.name.decode())
            item.setData(entry, Qt.ItemDataRole.UserRole)
            model.appendRow([item, QStandardItem(str(entry.info.meta.size)), QStandardItem(
                ftype), QStandardItem(str(datetime.datetime.fromtimestamp((entry.info.meta.mtime))))])

    @Slot(QModelIndex)
    def filesViewDoubleClicked(self, index: QModelIndex):
        entry = index.data(Qt.ItemDataRole.UserRole)
        if not isinstance(entry, pytsk3.File):
            return

        if entry.info.meta.type == pytsk3.TSK_FS_META_TYPE_REG:
            if entry.info.meta.size > 0:
                raw = entry.read_random(0, entry.info.meta.size)
                self.hexview.upload(BytesIO(raw))
                self.textview.upload(BytesIO(raw))
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
        self.evidenceTree.model().upload(path)
