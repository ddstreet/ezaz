
from .command import SimpleCommand


class LoginCommand(SimpleCommand):
    @classmethod
    def command_name_list(cls):
        return ['login']

    def login(self, **opts):
        from ..azobject.account import Account
        return Account.get_instance(**opts).login(**opts)
