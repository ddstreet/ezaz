
from .command import AzObjectActionCommand


class UserCommand(AzObjectActionCommand):
    @classmethod
    def azclass(cls):
        from ..azobject.user import User
        return User

    @classmethod
    def get_default_action(cls):
        return 'signed_in_user'
