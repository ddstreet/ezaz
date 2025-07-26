
from functools import cached_property

from ..azobject.account import Account
from .account import AccountCommand
from .command import SimpleCommand


class LogoutCommand(SimpleCommand):
    @classmethod
    def command_name_list(cls):
        return ['logout']

    @cached_property
    def account(self):
        return Account(cache=self._cache, config=self._config, verbose=self.verbose, dry_run=self.dry_run)

    def run(self):
        AccountCommand.cls_logout(self.account)
