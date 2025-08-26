
from .command import AzFilterer
from .command import AzSubObjectActionCommand


class ResourceGroupCommand(AzFilterer, AzSubObjectActionCommand):
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
