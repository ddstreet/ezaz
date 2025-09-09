
from contextlib import suppress
from functools import cached_property

from ..argutil import PositionalArgConfig
from ..exception import EzazException
from .command import SimpleCommand


class DirectCommand(SimpleCommand):
    @classmethod
    def command_name_list(cls):
        return ['az']

    @classmethod
    def get_command_preparser(cls):
        def preparser(args):
            with suppress(ValueError):
                args.insert(args.index('az') + 1, '--')
            return args
        return preparser

    @classmethod
    def get_simple_command_argconfigs(cls):
        return [*super().get_simple_command_argconfigs(),
                PositionalArgConfig('command', remainder=True, help='Command to run (i.e. az COMMAND ...)')]

    @cached_property
    def direct(self):
        from ..azobject.direct import DirectAction
        return DirectAction(verbose=self.verbose, dry_run=self.dry_run)

    def az(self, command, **opts):
        if command and command[0] == '--':
            command = command[1:]
        if not command:
            raise EzazException('Must provide az command')
        self.direct.az(*command)
