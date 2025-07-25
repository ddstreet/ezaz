
from .command import AzObjectActionCommand


class StorageContainerCommand(AzObjectActionCommand):
    @classmethod
    def azclass(cls):
        from ..azobject.storagecontainer import StorageContainer
        return StorageContainer
