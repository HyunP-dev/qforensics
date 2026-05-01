from __future__ import annotations

from io import BytesIO

import pyregf
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from qforensics.type import tree


class HiveKeyRootItem:
    def __init__(self):
        self.children = []


class HiveKeyItem(tree.Node):
    def __init__(self, parent, key):
        super().__init__(parent)
        self.key = key
        self._children = []
        self._is_initialized = False

    @property
    def children(self):
        if self.key is None:
            return []

        if not self._is_initialized:
            n = self.key.get_number_of_sub_keys()
            for i in range(n):
                subkey = self.key.get_sub_key(i)
                print(subkey)
                self._children.append(HiveKeyItem(self, subkey))
            self._is_initialized = True

        return self._children

    @children.setter
    def children(self, o):
        pass


class HiveKeyModel(QAbstractItemModel):
    def __init__(self, io):
        super().__init__()
        self.root_item = HiveKeyRootItem()
        handle: pyregf.file = pyregf.file()
        handle.open_file_object(io)
        self.root_item.children.append(
            HiveKeyItem(self.root_item, handle.get_root_key())
        )

    def columnCount(self, parent=QModelIndex()):
        return 1

    def rowCount(self, parent=QModelIndex()) -> int:
        if not parent.isValid():
            return 1
        else:
            parent_item = parent.internalPointer()

        return parent_item.key.get_number_of_sub_keys()

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        if role == Qt.ItemDataRole.DisplayRole:
            item = index.internalPointer()
            if isinstance(item, HiveKeyItem):
                return item.key.get_name()
            return None
        
        if role == Qt.ItemDataRole.DecorationRole:
            return QIcon("images/icons/folder.png")
        return None

    def index(self, row, column, parent=QModelIndex()):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        if not parent.isValid():
            parent_item = self.root_item
        else:
            parent_item = parent.internalPointer()

        if isinstance(parent_item, tree.Node) or isinstance(
            parent_item, HiveKeyRootItem
        ):
            child_item = parent_item.children[row]
            if child_item:
                return self.createIndex(row, column, child_item)
        return QModelIndex()

    def parent(self, index: QModelIndex):
        if not index.isValid():
            return QModelIndex()

        child_item = index.internalPointer()
        parent_item = child_item.parent

        if parent_item == self.root_item or parent_item is None:
            return QModelIndex()

        return self.createIndex(parent_item.row(), 0, parent_item)

class HiveValueModel(QAbstractTableModel):
    VALUES_TYPE = {v: k for k, v in pyregf.value_types.__dict__.items()}

    def __init__(self, key, parent=None):
        super().__init__(parent)
        self.key = key

    def columnCount(self, parent=QModelIndex()):
        return 3
    
    def rowCount(self, parent=QModelIndex()):
        return self.key.get_number_of_values()
    
    def data(self, index:QModelIndex, role=Qt.ItemDataRole):
        value = self.key.get_value(index.row())
        type_str = self.VALUES_TYPE[value.get_type()]
        if role == Qt.ItemDataRole.DisplayRole:
            match index.column():
                case 0:
                    return value.get_name() or "(Default)"
                case 1:
                    return type_str
                case 2:
                    if value.get_type() == pyregf.value_types.STRING:
                        return value.get_data_as_string() or ""
                    if value.get_type() == pyregf.value_types.BINARY_DATA:
                        return value.get_data().hex(" ")
                    if "INTEGER" in type_str:
                        return hex(value.get_data_as_integer())
                    return str(value.get_data())
        if role == Qt.ItemDataRole.DecorationRole and index.column() == 0:
            if value.get_type() == pyregf.value_types.STRING:
                return QIcon("images/icons/document-attribute-s.png")
            if value.get_type() == pyregf.value_types.BINARY_DATA:
                return QIcon("images/icons/document-binary.png")
            if "INTEGER" in type_str:
                return QIcon("images/icons/document-number-1.png")
            return QIcon("images/icons/document.png")

    def headerData(self, section, orientation, /, role=...):
        if orientation == Qt.Orientation.Horizontal:
            if role == Qt.ItemDataRole.DisplayRole:
                return ["Name", "Type", "Data"][section]



class HiveViewer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setLayout(layout:=QVBoxLayout())
        layout.setContentsMargins(0, 0, 0, 0)

        self.splitter = QSplitter()
        self.splitter.setContentsMargins(0, 0, 0, 0)
        
        self.keyView = QTreeView()
        self.keyView.setHeaderHidden(True)

        self.valueView = QTreeView()
        self.valueView.setRootIsDecorated(False)

        self.keyView.doubleClicked.connect(self.keyView_doubleClicked)

        self.splitter.addWidget(self.keyView)
        self.splitter.addWidget(self.valueView)

        self.splitter.setSizes([300, 750])

        layout.addWidget(self.splitter)
    
    @Slot(QModelIndex)
    def keyView_doubleClicked(self, index: QModelIndex):
        key = index.internalPointer().key
        self.valueView.setModel(HiveValueModel(key))

    def parse(self, io):
        model = HiveKeyModel(io)
        self.keyView.setModel(model)

def main():
    app = QApplication()
    # window = QMainWindow()
    # window.show()
    viewer = HiveViewer(None)

    with open("D:\\Personal\\software", "rb") as f:
        model = HiveKeyModel(BytesIO(f.read()))

    viewer.keyView.setModel(model)
    
    viewer.show()
    app.exec()


if __name__ == "__main__":
    main()
