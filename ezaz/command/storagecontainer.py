
from ..azobject.storagecontainer import StorageContainer
from .command import CommonActionCommand
from .storageaccount import StorageAccountCommand


class StorageContainerCommand(CommonActionCommand):
    @classmethod
    def parent_command_cls(cls):
        return StorageAccountCommand

    @classmethod
    def azclass(cls):
        return StorageContainer
