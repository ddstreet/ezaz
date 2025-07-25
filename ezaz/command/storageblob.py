
from ..azobject.storageblob import StorageBlob
from .command import AllActionCommand
from .storagecontainer import StorageContainerCommand


class StorageBlobCommand(AllActionCommand):
    @classmethod
    def parent_command_cls(cls):
        return StorageContainerCommand

    @classmethod
    def azobject_class(cls):
        return StorageBlob
