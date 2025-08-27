
from .command import AzObjectActionCommand


class AccountCommand(AzObjectActionCommand):
    @classmethod
    def azclass(cls):
        from ..azobject.account import Account
        return Account
