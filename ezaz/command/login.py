
from functools import cached_property
from types import SimpleNamespace

from .account import AccountCommand
from .command import SimpleCommand


class LoginCommand(SimpleCommand):
    @classmethod
    def command_name_list(cls):
        return ['login']

    @cached_property
    def account_command(self):
        return AccountCommand(options=SimpleNamespace(**self.opts, action='login'),
                              config=self.config,
                              cache=self.cache)

    def run(self):
        self.account_command.run()
