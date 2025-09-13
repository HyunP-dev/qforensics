from __future__ import annotations

from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from qforensics.model import *
from qforensics.model.evidencemodel import *

from qforensics.widget import *
from qforensics.type.tskwrapper import TSKBytesIO


import datetime
from io import BytesIO
import platform
import os




class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.addToolBar(toolbar := QToolBar())
        toolbar.setFloatable(False)
        toolbar.setMovable(False)
        toolbar.setFixedHeight(24)
        attachAction = QAction("이미지 탑재", self)
        attachAction.setIcon(
            QIcon(os.path.join(__file__, "..", "resources/icons/drive--plus.png")))
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
        self.evidenceTree.setEditTriggers(QTreeView.NoEditTriggers)

        self.leftPanel = QWidget()
        self.leftPanel.setLayout(QVBoxLayout())
        self.leftPanel.layout().setContentsMargins(0, 0, 0, 0)
        self.leftTabs = QTabWidget()
        self.leftPanel.layout().addWidget(self.leftTabs)
        self.leftTabs.addTab(self.evidenceTree, "탐색 트리")

        self.resultTree = QTreeView()
        self.resultTree.setModel(ArtifactModel())
        self.resultTree.setHeaderHidden(True)
        self.resultTree.setEditTriggers(QTreeView.NoEditTriggers)
        self.resultTree.expandAll()
        self.resultTree.doubleClicked.connect(self.resultViewDoubleClicked)
        self.leftTabs.addTab(self.resultTree, "분석 트리")

        self.leftTabs.tabBarClicked.connect(self.leftTabBarClicked)

        rightPanel = QWidget()
        rightPanel.setLayout(QVBoxLayout())
        rightPanel.layout().setContentsMargins(0, 0, 0, 0)
        rightTabs = QTabWidget()
        rightPanel.layout().addWidget(rightTabs)
        filesView = QTreeView()
        self.filesView = filesView
        filesView.setEditTriggers(QTreeView.NoEditTriggers)
        filesView.setRootIsDecorated(False)
        rightTabs.addTab(self.filesView, "파일 목록")
        filesView.doubleClicked.connect(self.filesViewDoubleClicked)
        self.explorerRightPanel = rightPanel

        self.splitter = QSplitter()
        self.splitter.addWidget(self.leftPanel)

        rightSplitter = QSplitter()
        rightSplitter.setOrientation(Qt.Orientation.Vertical)
        rightSplitter.addWidget(self.explorerRightPanel)

        self.explorerRightSplitter = rightSplitter

        viewerTabs = QTabWidget()
        self.hexview = HexViewer()
        viewerTabs.addTab(self.hexview, "Hex")
        self.textview = TextViewer()
        viewerTabs.addTab(self.textview, "문자열")
        self.viewerTabs = viewerTabs
        rightSplitter.addWidget(viewerTabs)

        self.splitter.addWidget(rightSplitter)

        resultRightView = QWidget()
        self.splitter.addWidget(resultRightView)
        resultRightView.hide()
        self.resultRightView = resultRightView

        self.splitter.setStretchFactor(0, 3)
        self.splitter.setStretchFactor(1, 7)
        self.setCentralWidget(self.splitter)
        self.resize(1000, 600)

    @Slot(int)
    def leftTabBarClicked(self, index):
        print(index)

    def showFiles(self, *directories):
        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(["파일명", "크기", "타입", "변경 시간"])
        self.filesView.setModel(model)
        for directory in directories:
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
                if entry.info.meta is not None:
                    model.appendRow([item, QStandardItem(str(entry.info.meta.size)), QStandardItem(
                        ftype), QStandardItem(str(datetime.datetime.fromtimestamp((entry.info.meta.mtime))))])
                else:
                    model.appendRow([item, QStandardItem(""), QStandardItem(ftype), QStandardItem("")])


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
        self.showFiles(directory)
        
        

    @Slot(QModelIndex)
    def filesViewDoubleClicked(self, index: QModelIndex):
        entry = index.data(Qt.ItemDataRole.UserRole)
        if not isinstance(entry, pytsk3.File):
            return

        tabs_count = self.viewerTabs.count()
        if tabs_count > 2:
            for i in reversed(range(2, tabs_count)):
                self.viewerTabs.removeTab(i)

        if entry.info.meta.type == pytsk3.TSK_FS_META_TYPE_REG:
            stream = TSKBytesIO(entry)
            stream.seek(4)
            if stream.read(4) == b"SCCA":
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
