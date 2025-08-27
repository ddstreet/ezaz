
from .command import AzCommonActionCommand


class UserCommand(AzCommonActionCommand):
    @classmethod
    def azclass(cls):
        from ..azobject.user import User
        return User
