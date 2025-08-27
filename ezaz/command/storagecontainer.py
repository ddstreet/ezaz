
from .command import AzCommonActionCommand


class StorageContainerCommand(AzCommonActionCommand):
    @classmethod
    def parent_command_cls(cls):
        from .storageaccount import StorageAccountCommand
        return StorageAccountCommand

    @classmethod
    def azclass(cls):
        from ..azobject.storagecontainer import StorageContainer
        return StorageContainer
