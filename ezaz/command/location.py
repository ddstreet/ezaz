
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

    @classmethod
    def parser_add_argument_azobject_id(cls, parser, parent=False):
        # We don't want the --subscription argument
        cls._parser_add_argument_azobject_id(parser, parent)
