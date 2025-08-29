
from .command import AzCommonActionCommand


class UserCommand(AzCommonActionCommand):
    @classmethod
    def azclass(cls):
        from ..azobject.user import User
        return User

    @classmethod
    def get_default_action(cls):
        return 'signed_in_user'
