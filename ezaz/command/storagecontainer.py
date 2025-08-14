
from .command import AzSubObjectActionCommand


class StorageContainerCommand(AzSubObjectActionCommand):
    @classmethod
    def parent_command_cls(cls):
        from .storageaccount import StorageAccountCommand
        return StorageAccountCommand

    @classmethod
    def azclass(cls):
        from ..azobject.storagecontainer import StorageContainer
        return StorageContainer
