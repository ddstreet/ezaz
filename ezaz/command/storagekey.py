
from .command import AzCommonActionCommand


class StorageKeyCommand(AzCommonActionCommand):
    @classmethod
    def parent_command_cls(cls):
        from .storageaccount import StorageAccountCommand
        return StorageAccountCommand

    @classmethod
    def azclass(cls):
        from ..azobject.storagekey import StorageKey
        return StorageKey
