
from ..azobject.resourcegroup import ResourceGroup
from .command import AzSubObjectActionCommand
from .subscription import SubscriptionCommand


class ResourceGroupCommand(AzSubObjectActionCommand):
    @classmethod
    def parent_command_cls(cls):
        return SubscriptionCommand

    @classmethod
    def azclass(cls):
        return ResourceGroup

    @classmethod
    def aliases(cls):
        return ['group', 'rg']

    @classmethod
    def parser_add_delete_action_arguments(cls, parser):
        parser.add_argument('-y', '--yes',
                            action='store_true',
                            help='Do not prompt for confirmation')
        parser.add_argument('--no-wait',
                            action='store_true',
                            help='Do not wait for long-running operation to finish')
