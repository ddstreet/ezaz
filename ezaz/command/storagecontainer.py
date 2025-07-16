
from .command import AllActionCommand
from .storageaccount import StorageAccountCommand


class StorageContainerCommand(AllActionCommand):
    @classmethod
    def parent_command_cls(cls):
        return StorageAccountCommand

    @classmethod
    def command_name_list(cls):
        return ['storage', 'container']
