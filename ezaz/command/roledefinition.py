
from .command import AzSubObjectActionCommand


class RoleDefinitionCommand(AzSubObjectActionCommand):
    @classmethod
    def parent_command_cls(cls):
        from .subscription import SubscriptionCommand
        return SubscriptionCommand

    @classmethod
    def azclass(cls):
        from ..azobject.roledefinition import RoleDefinition
        return RoleDefinition
