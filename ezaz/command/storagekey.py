
from .command import AzSubObjectActionCommand


class StorageKeyCommand(AzSubObjectActionCommand):
    @classmethod
    def parent_command_cls(cls):
        from .storageaccount import StorageAccountCommand
        return StorageAccountCommand

    @classmethod
    def azclass(cls):
        from ..azobject.storagekey import StorageKey
        return StorageKey
