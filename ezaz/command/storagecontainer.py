
from .command import StorageAccountSubCommand
from .command import StandardActionCommand


class StorageContainerCommand(StorageAccountSubCommand, StandardActionCommand):
    ACTION_ARGUMENT_NAME = 'storage container'
    ACTION_ARGUMENT_METAVAR = 'CONTAINER'
    ACTION_ATTR_NAME = 'storage_container'

    @classmethod
    def name(cls):
        return 'storagecontainer'

    def _show(self, storage_containter):
        info = storage_containter.storage_containter_info
        msg = info.name
        if self.verbose:
            msg += f' (location: {info.location})'
        print(msg)

