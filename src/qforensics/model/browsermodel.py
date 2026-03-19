from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

import pytsk3

import datetime


class TSKFileBrowserModel(QAbstractTableModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._curdir = None
        self._internal_entries = []

    @staticmethod
    def fstype_to_string(type_):
        ftype = ""
        if type_ == pytsk3.TSK_FS_NAME_TYPE_UNDEF:
            ftype = "Unknown type"
        if type_ == pytsk3.TSK_FS_NAME_TYPE_FIFO:
            ftype = "Named pipe"
        if type_ == pytsk3.TSK_FS_NAME_TYPE_CHR:
            ftype = "Character device"
        if type_ == pytsk3.TSK_FS_META_TYPE_DIR:
            ftype = "Directory"
        if type_ == pytsk3.TSK_FS_META_TYPE_BLK:
            ftype = "Block device"
        if type_ == pytsk3.TSK_FS_META_TYPE_REG:
            ftype = "Regular file"
        if type_ == pytsk3.TSK_FS_META_TYPE_LNK:
            ftype = "Symbolic link"
        if type_ == pytsk3.TSK_FS_META_TYPE_SOCK:
            ftype = "Socket"
        if type_ == pytsk3.TSK_FS_NAME_TYPE_SHAD:
            ftype = "Shadow inode (solaris)"
        if type_ == pytsk3.TSK_FS_NAME_TYPE_WHT:
            ftype = "Whiteout (openbsd)"
        if type_ == pytsk3.TSK_FS_NAME_TYPE_VIRT:
            ftype = 'Special (TSK added "Virtual" files)'
        if type_ == pytsk3.TSK_FS_NAME_TYPE_VIRT_DIR:
            ftype = 'Special (TSK added "Virtual" directories)'
        return ftype

    def open_dir(self, directory):
        self._curdir = directory

        for entry in directory:
            if entry.info.name.name in [b".", b".."]:
                continue
            if entry.info.meta is not None:  # 이것도 나중에 핸들링해야 하지 않나.
                self._internal_entries.append(entry)

    def columnCount(self, parent=QModelIndex()):
        return 4

    def rowCount(self, parent=QModelIndex()):
        return len(self._internal_entries)

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        entry = self._internal_entries[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            match index.column():
                case 0:
                    return entry.info.name.name.decode()
                case 1:
                    return str(entry.info.meta.size)
                case 2:
                    return TSKFileBrowserModel.fstype_to_string(entry.info.meta.type)
                case 3:
                    return str(datetime.datetime.fromtimestamp((entry.info.meta.mtime)))

        if role == Qt.ItemDataRole.UserRole:
            return entry
    
    def headerData(self, section, orientation, /, role = ...):
        if orientation == Qt.Orientation.Horizontal:
            if role == Qt.ItemDataRole.DisplayRole:
                return ["파일명", "크기", "타입", "변경 시간"][section]
