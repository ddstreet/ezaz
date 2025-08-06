
from ..azobject.storageblob import StorageBlob
from .command import AzSubObjectActionCommand
from .storagecontainer import StorageContainerCommand


class StorageBlobCommand(AzSubObjectActionCommand):
    @classmethod
    def parent_command_cls(cls):
        return StorageContainerCommand

    @classmethod
    def azclass(cls):
        return StorageBlob
