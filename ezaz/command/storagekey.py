
from .command import AzObjectActionCommand


class StorageKeyCommand(AzObjectActionCommand):
    @classmethod
    def azclass(cls):
        from ..azobject.storagekey import StorageKey
        return StorageKey
