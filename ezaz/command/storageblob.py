
from .command import AzSubObjectActionCommand


class StorageBlobCommand(AzSubObjectActionCommand):
    @classmethod
    def parent_command_cls(cls):
        from .storagecontainer import StorageContainerCommand
        return StorageContainerCommand

    @classmethod
    def azclass(cls):
        from ..azobject.storageblob import StorageBlob
        return StorageBlob
