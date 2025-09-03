from __future__ import annotations

from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *
import pyewf

from qforensics.handler import *
from qforensics.type import tree

import os


class EWFImageItem(tree.Node):
    def __init__(self, path, parent):
        super().__init__(parent)
        self.path = path
        filenames = pyewf.glob(path)
        ewf_handle = pyewf.handle()
        ewf_handle.open(filenames)
        img_info = ewf_Img_Info(ewf_handle)
        self.filesystems = []
        for p in pytsk3.Volume_Info(img_info):
            # print(p.addr, p.desc, p.flags, p.len, p.next, p.start, p.table_num)
            volume_item = VolumeItem(p, self, p.desc.decode())
            self.children.append(volume_item)
            
            try:
                fs_info = pytsk3.FS_Info(img_info, offset=p.start * 512)
                self.filesystems.append(fs_info) # 이렇게 저장해두지 않으면 메모리에서 해제됨 ㅋㅋㅋ
                # vbr = img_info.read(p.start * 512, 512)
                root_dir = fs_info.open_dir("/", 2)
                volume_item.root_directory = root_dir
                for entry in root_dir:
                    if entry.info.name.name in [b".", b".."]:
                        continue

                    if entry.info.meta and entry.info.meta.type == pytsk3.TSK_FS_META_TYPE_DIR:
                        try:
                            volume_item.children.append(DirectoryItem(entry, volume_item))
                        except Exception as e:
                            print(e)
                
            except:
                pass
    
    def __str__(self):
        return os.path.basename(self.path)

class DirectoryItem(tree.Node):
    def __init__(self, entry: pytsk3.File, parent):
        super().__init__(parent)
        self.parent = parent
        self.entry = entry
        self._is_initialized = False
        self._children = []

    @property
    def children(self):
        if not self._is_initialized:
            if self.entry.info.meta and self.entry.info.meta.type == pytsk3.TSK_FS_META_TYPE_DIR:
                if isinstance(self.entry, pytsk3.File):
                    directory = self.entry.as_directory()
                    for entry in directory:
                        dirname = entry.info.name.name.decode()
                        if dirname == "." or dirname == "..":
                            continue
                        if entry.info.meta and entry.info.meta.type == pytsk3.TSK_FS_META_TYPE_DIR:
                            self._children.append(DirectoryItem(entry, self))
                    self._is_initialized = True
            return self._children
        return self._children
    
    @children.setter
    def children(self, o):
        pass

    def __str__(self):
        return self.entry.info.name.name.decode()

class VolumeItem(tree.Node):
    def __init__(self, partition: pytsk3.TSK_VS_PART_INFO, parent: EWFImageItem, desc: str):
        super().__init__(parent)
        self.partition = partition
        self.desc = desc
        self.root_directory = None

    def __str__(self):
        return str(self.desc)
    
        
class EvidenceTreeRootItem:
    def __init__(self):
        self.children = []

class EvidenceTreeModel(QAbstractItemModel):
    def __init__(self):
        super().__init__()
        self.root_item = EvidenceTreeRootItem()
    
    def upload(self, path):
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        self.root_item.children.append(EWFImageItem(path, self.root_item))
        self.endInsertRows()

    def columnCount(self, parent=QModelIndex()):
        return 1

    def rowCount(self, parent=QModelIndex()):
        if not parent.isValid():
            parent_item = self.root_item
        else:
            parent_item = parent.internalPointer()
        
        if type(parent_item) == EvidenceTreeRootItem:
            return parent_item.children.__len__()
        
        if isinstance(parent_item, tree.Node):
            return parent_item.children.__len__()
        
        return 0

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        if role == Qt.DisplayRole:
            item = index.internalPointer()
            if isinstance(item, tree.Node):
                return str(item)
            return item
        return None

    def index(self, row, column, parent=QModelIndex()):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        if not parent.isValid():
            parent_item = self.root_item
        else:
            parent_item = parent.internalPointer()

        if type(parent_item) == EvidenceTreeRootItem:
            child_item = parent_item.children[row]
            if child_item:
                return self.createIndex(row, column, child_item)
        if isinstance(parent_item, tree.Node):
            child_item = parent_item.children[row]
            if child_item:
                return self.createIndex(row, column, child_item)
        return QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()

        child_item = index.internalPointer()
        parent_item = child_item.parent

        if parent_item == self.root_item or parent_item is None:
            return QModelIndex()

        return self.createIndex(parent_item.row(), 0, parent_item)