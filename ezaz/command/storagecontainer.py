
from .command import DefineSubCommand
from .storageaccount import StorageAccountSubCommand


class StorageContainerCommand(StorageAccountSubCommand):
    @classmethod
    def command_name_list(cls):
        return ['storage', 'container']

    def _show(self, storage_containter):
        info = storage_containter.info
        msg = info.name
        if self.verbose:
            msg += f' (location: {info.location})'
        print(msg)


StorageContainerSubCommand = DefineSubCommand(StorageAccountSubCommand, StorageContainerCommand)
