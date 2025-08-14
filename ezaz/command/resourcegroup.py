
from .command import AzSubObjectActionCommand


class ResourceGroupCommand(AzSubObjectActionCommand):
    @classmethod
    def parent_command_cls(cls):
        from .subscription import SubscriptionCommand
        return SubscriptionCommand

    @classmethod
    def azclass(cls):
        from ..azobject.resourcegroup import ResourceGroup
        return ResourceGroup

    @classmethod
    def aliases(cls):
        return ['group', 'rg']
