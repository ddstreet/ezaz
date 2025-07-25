
from ..argutil import ArgMap
from .command import AzSubObjectActionCommand


class UserCommand(AzSubObjectActionCommand):
    @classmethod
    def parent_command_cls(cls):
        from .account import AccountCommand
        return AccountCommand

    @classmethod
    def azclass(cls):
        from ..azobject.user import User
        return User
