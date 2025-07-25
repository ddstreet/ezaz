
from ..azobject.storagecontainer import StorageContainer
from .command import AzSubObjectActionCommand
from .storageaccount import StorageAccountCommand


class StorageContainerCommand(AzSubObjectActionCommand):
    @classmethod
    def parent_command_cls(cls):
        return StorageAccountCommand

    @classmethod
    def azclass(cls):
        return StorageContainer
