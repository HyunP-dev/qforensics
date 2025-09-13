import os
import pytsk3

from qforensics.type.io import AbstractROBytesIO


class TSKBytesIO(AbstractROBytesIO):
    def __init__(self, entry: pytsk3.File):
        self._entry = entry
        self._offset = 0
        self._size = self._entry.info.meta.size

    def read(self, size=-1) -> bytes:
        if size == -1:
            self._offset = self._size()
            return self._entry.read_random(self._offset, self._size - self._offset)
        if self._offset + size >= self._size:
            size = self._size - self._offset
        print(self._offset, size)
        if size == 0:
            return bytes([])
        raw = self._entry.read_random(self._offset, size)
        self._offset += size
        return raw

    def tell(self) -> int:
        return self._offset

    def seek(self, offset, whence=os.SEEK_SET):
        match whence:
            case os.SEEK_SET:
                self._offset = offset
                return
            case os.SEEK_CUR:
                self._offset += offset
                return
            case os.SEEK_END:
                self._offset = self._entry.info.meta.size - offset
                return

    def seekable(self) -> bool:
        return True
