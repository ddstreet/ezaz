
from .command import AzCommonActionCommand


class StorageKeyCommand(AzCommonActionCommand):
    @classmethod
    def azclass(cls):
        from ..azobject.storagekey import StorageKey
        return StorageKey
