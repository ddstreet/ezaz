
from ..azobject.storagekey import StorageKey
from .command import AzSubObjectActionCommand
from .storageaccount import StorageAccountCommand


class StorageKeyCommand(AzSubObjectActionCommand):
    @classmethod
    def parent_command_cls(cls):
        return StorageAccountCommand

    @classmethod
    def azclass(cls):
        return StorageKey

    @classmethod
    def command_name_list(cls):
        return ['storage', 'key']
