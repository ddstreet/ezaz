
from ..azobject.storageaccount import StorageAccount
from .command import AllActionCommand
from .resourcegroup import ResourceGroupCommand


class StorageAccountCommand(AllActionCommand):
    @classmethod
    def parent_command_cls(cls):
        return ResourceGroupCommand

    @classmethod
    def azobject_class(cls):
        return StorageAccount
