
from ..azobject.storagekey import StorageKey
from .command import ListActionCommand
from .command import ShowActionCommand
from .storageaccount import StorageAccountCommand


class StorageKeyCommand(ListActionCommand, ShowActionCommand):
    @classmethod
    def parent_command_cls(cls):
        return StorageAccountCommand

    @classmethod
    def azobject_class(cls):
        return StorageKey

    @classmethod
    def command_name_list(cls):
        return ['storage', 'key']
