
from ..azobject.storagecontainer import StorageContainer
from .command import AllActionCommand
from .storageaccount import StorageAccountCommand


class StorageContainerCommand(AllActionCommand):
    @classmethod
    def parent_command_cls(cls):
        return StorageAccountCommand

    @classmethod
    def azobject_class(cls):
        return StorageContainer
