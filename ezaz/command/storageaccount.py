
from .command import AllActionCommand
from .resourcegroup import ResourceGroupCommand


class StorageAccountCommand(AllActionCommand):
    @classmethod
    def parent_command_cls(cls):
        return ResourceGroupCommand

    @classmethod
    def command_name_list(cls):
        return ['storage', 'account']
