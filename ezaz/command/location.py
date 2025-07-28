
from ..azobject.location import Location
from .command import ShowActionCommand
from .command import ListActionCommand
from .subscription import SubscriptionCommand


class LocationCommand(ShowActionCommand, ListActionCommand):
    @classmethod
    def parent_command_cls(cls):
        return SubscriptionCommand

    @classmethod
    def azobject_class(cls):
        return Location

    @classmethod
    def parser_add_argument_azobject_id(cls, parser, parent=False):
        cls._parser_add_argument_azobject_id(parser, parent)
