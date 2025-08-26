
from .command import AzSubObjectActionCommand


class LocationCommand(AzSubObjectActionCommand):
    @classmethod
    def parent_command_cls(cls):
        from .subscription import SubscriptionCommand
        return SubscriptionCommand

    @classmethod
    def azclass(cls):
        from ..azobject.location import Location
        return Location
