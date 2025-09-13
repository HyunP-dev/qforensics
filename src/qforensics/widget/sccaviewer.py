from io import *

import pyscca

from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from qforensics.type.io import AbstractROBytesIO

class TableView(QWidget):
    def __init__(self, title):
        super().__init__()
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        header = QWidget()
        header.setLayout(QHBoxLayout())
        header.layout().addWidget(QLabel(title))
        header.layout().setContentsMargins(10, 0, 10, 0)
        # self.layout().addWidget(header)

        self._treeview = QTreeView()
        self._treeview.setEditTriggers(QTreeView.NoEditTriggers)
        self.layout().addWidget(self._treeview)
    
    @property
    def model(self):
        return self._treeview.model()
    
    @model.setter
    def model(self, model):
        self._treeview.setModel(model)


class SCCAViewer(QSplitter):
    def __init__(self):
        super().__init__()
        self.setOrientation(Qt.Orientation.Vertical)
        self.volumesView = TableView("Volumes")
        self.timesView = TableView("Last Run Time")
        self.filesView = TableView("Files")
        self.addWidget(self.timesView)
        self.addWidget(self.filesView)
        self.addWidget(self.volumesView)

    
    def parse(self, stream: AbstractROBytesIO):
        handle = pyscca.file()
        handle.open_file_object(stream)
        nnames = handle.get_number_of_filenames()
        
        filesModel = QStandardItemModel()
        filesModel.setHorizontalHeaderLabels(["Filename"])
        for i in range(nnames):
            filesModel.appendRow(QStandardItem(handle.get_filename(i)))
        self.filesView.model = filesModel

        timesModel = QStandardItemModel()
        timesModel.setHorizontalHeaderLabels(["Last Run Time"])
        ntimes = handle.get_run_count()
        print(ntimes)
        for i in range(ntimes):
            try:
                last_time = handle.get_last_run_time(i)
                timesModel.appendRow(QStandardItem(str(last_time)))
            except:
                break
            if not last_time:
                break
            print(last_time)
        self.timesView.model = timesModel
        


