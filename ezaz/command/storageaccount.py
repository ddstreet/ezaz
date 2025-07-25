
from .command import AzSubObjectActionCommand


class StorageAccountCommand(AzSubObjectActionCommand):
    @classmethod
    def parent_command_cls(cls):
        from .resourcegroup import ResourceGroupCommand
        return ResourceGroupCommand

    @classmethod
    def azclass(cls):
        from ..azobject.storageaccount import StorageAccount
        return StorageAccount
