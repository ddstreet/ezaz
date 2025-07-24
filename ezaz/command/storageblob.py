
from .command import AllActionCommand
from .storagecontainer import StorageContainerCommand


class StorageBlobCommand(AllActionCommand):
    @classmethod
    def parent_command_cls(cls):
        return StorageContainerCommand

    @classmethod
    def command_name_list(cls):
        return ['storage', 'blob']
