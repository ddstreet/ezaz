
from ..azobject.storageaccount import StorageAccount
from .command import AzSubObjectActionCommand
from .resourcegroup import ResourceGroupCommand


class StorageAccountCommand(AzSubObjectActionCommand):
    @classmethod
    def parent_command_cls(cls):
        return ResourceGroupCommand

    @classmethod
    def azclass(cls):
        return StorageAccount
