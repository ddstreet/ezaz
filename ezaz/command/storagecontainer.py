
from .command import SubCommand
from .storageaccount import StorageAccountCommand


class StorageContainerCommand(SubCommand):
    @classmethod
    def parent_command_cls(cls):
        return StorageAccountCommand

    @classmethod
    def command_name_list(cls):
        return ['storage', 'container']

    def _show(self, storage_containter):
        info = storage_containter.info
        msg = info.name
        print(msg)
