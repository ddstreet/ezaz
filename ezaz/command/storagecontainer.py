
from .command import AzCommonActionCommand


class StorageContainerCommand(AzCommonActionCommand):
    @classmethod
    def azclass(cls):
        from ..azobject.storagecontainer import StorageContainer
        return StorageContainer
