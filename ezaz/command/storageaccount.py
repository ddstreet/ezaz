
from ..azobject.storageaccount import StorageAccount
from .command import AzSubObjectActionCommand
from .resourcegroup import ResourceGroupCommand


class StorageAccountCommand(AzSubObjectActionCommand):
    @classmethod
    def parent_command_cls(cls):
        return ResourceGroupCommand

    @classmethod
    def azclass(cls):
        return StorageAccount

    @classmethod
    def parser_add_delete_action_arguments(cls, parser):
        parser.add_argument('-y', '--yes',
                            action='store_true',
                            help='Do not prompt for confirmation')
