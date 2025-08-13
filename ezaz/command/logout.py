
from functools import cached_property
from types import SimpleNamespace

from .account import AccountCommand
from .command import SimpleCommand


class LogoutCommand(SimpleCommand):
    @classmethod
    def command_name_list(cls):
        return ['logout']

    @cached_property
    def account_command(self):
        return AccountCommand(options=SimpleNamespace(**self.opts, action='logout'),
                              config=self.config,
                              cache=self.cache)

    def run(self):
        self.account_command.run()
