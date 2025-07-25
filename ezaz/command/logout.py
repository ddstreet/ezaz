
from .command import SimpleCommand


class LogoutCommand(SimpleCommand):
    @classmethod
    def command_name_list(cls):
        return ['logout']

    def logout(self, **opts):
        from ..azobject.user import User
        return User.get_null_instance(**opts).logout(**opts)
