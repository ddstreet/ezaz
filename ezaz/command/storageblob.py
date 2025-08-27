
from .command import AzCommonActionCommand


class StorageBlobCommand(AzCommonActionCommand):
    @classmethod
    def azclass(cls):
        from ..azobject.storageblob import StorageBlob
        return StorageBlob
