
from contextlib import suppress

from ..actionutil import ResponseTextHandler
from ..argutil import ArgMap
from ..azobject.account import Account
from ..exception import AlreadyLoggedIn
from ..exception import AlreadyLoggedOut
from ..exception import NotLoggedIn
from .command import AzObjectActionCommand


class AccountCommand(AzObjectActionCommand):
    @classmethod
    def azclass(cls):
        return Account

    def run_action_config_method(self):
        with suppress(AlreadyLoggedIn, AlreadyLoggedOut):
            super().run_action_config_method()
            return self.account_response()
        return self.account_response(already=True)

    def account_response(self, already=False):
        logged = 'Already logged' if already else 'Logged'
        try:
            info = self.azobject.info(**self.opts)
            return ResponseTextHandler(f"{logged} in as '{info.user.name}' using subscription '{info.name}' (id {info.id})")
        except NotLoggedIn:
            return ResponseTextHandler(f"{logged} out")
