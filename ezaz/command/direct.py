
import argparse

from functools import cached_property

from ..argutil import ArgConfig
from ..argutil import PositionalArgConfig
from .command import SimpleCommand


class DirectCommand(SimpleCommand):
    @classmethod
    def command_name_list(cls):
        return ['az']

    @classmethod
    def get_simple_command_argconfigs(cls):
        return [*super().get_simple_command_argconfigs(),
                PositionalArgConfig('command', help='Command to run (i.e. az COMMAND ...)'),
                PositionalArgConfig('args', remainder=True, help='Additional arguments and parameters')]

    @cached_property
    def direct(self):
        from ..azobject.direct import DirectAction
        return DirectAction(verbose=self.verbose, dry_run=self.dry_run)

    def az(self):
        self.direct.az(self.options.command, *self.options.args)
