
from .command import AzObjectActionCommand


class StorageBlobCommand(AzObjectActionCommand):
    @classmethod
    def azclass(cls):
        from ..azobject.storageblob import StorageBlob
        return StorageBlob
