from abc import ABCMeta, abstractmethod
import os


class AbstractROBytesIO(metaclass=ABCMeta):
    @abstractmethod
    def read(self, size=-1) -> bytes:
        pass
    
    @abstractmethod
    def tell(self) -> int:
        pass

    @abstractmethod
    def seek(self, offset, whence=os.SEEK_SET):
        pass

    def seekable(self) -> bool:
        return True
