
from .command import SimpleCommand


class LoginCommand(SimpleCommand):
    @classmethod
    def command_name_list(cls):
        return ['login']

    def login(self, **opts):
        from ..azobject.user import User
        return User.get_null_instance(**opts).login(**opts)
