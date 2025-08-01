
from ..azobject.location import Location
from .command import AzSubObjectActionCommand
from .subscription import SubscriptionCommand


class LocationCommand(AzSubObjectActionCommand):
    @classmethod
    def parent_command_cls(cls):
        return SubscriptionCommand

    @classmethod
    def azclass(cls):
        return Location

    @classmethod
    def parser_add_argument_azobject_id(cls, parser, parent=False):
        # We don't want the --subscription argument
        cls._parser_add_argument_azobject_id(parser, parent)
