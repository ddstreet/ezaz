
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
