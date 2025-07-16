
from ..azobject.account import Account
from .account import AccountCommand
from .command import SimpleCommand


class LogoutCommand(SimpleCommand):
    @classmethod
    def command_name_list(cls):
        return ['logout']

    def _setup(self):
        super()._setup()
        self._account = Account(self._config, verbose=self.verbose, dry_run=self.dry_run)

    def run(self):
        AccountCommand.cls_logout(self._account)
