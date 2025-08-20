
from functools import cached_property
from types import SimpleNamespace

from .command import SimpleCommand


class LoginCommand(SimpleCommand):
    @classmethod
    def command_name_list(cls):
        return ['login']

    @cached_property
    def account_command(self):
        from .account import AccountCommand
        return AccountCommand(options=SimpleNamespace(**self.opts, action='login'))

    def run(self):
        self.account_command.run()
