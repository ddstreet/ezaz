
from .command import SimpleCommand


class LogoutCommand(SimpleCommand):
    @classmethod
    def command_name_list(cls):
        return ['logout']

    def logout(self, **opts):
        from ..azobject.account import Account
        return Account.get_instance(**opts).logout(**opts)
