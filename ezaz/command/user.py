
from ..argutil import ArgMap
from .command import AzCommonActionCommand


class UserCommand(AzCommonActionCommand):
    @classmethod
    def parent_command_cls(cls):
        from .account import AccountCommand
        return AccountCommand

    @classmethod
    def azclass(cls):
        from ..azobject.user import User
        return User
