
import argparse

from functools import cached_property

from ..azobject.direct import DirectAction
from .command import SimpleCommand


class DirectCommand(SimpleCommand):
    @classmethod
    def command_name_list(cls):
        return ['az']

    @classmethod
    def parser_add_arguments(cls, parser):
        super().parser_add_arguments(parser)
        parser.add_argument('command', help='Command to run (i.e. "az COMMAND ...")')
        parser.add_argument('args', nargs=argparse.REMAINDER, help='Additional arguments and parameters')

    @cached_property
    def direct(self):
        return DirectAction(cache=self._cache, verbose=self.verbose, dry_run=self.dry_run)

    def run(self):
        self.direct.az(self._options.command, *self._options.args)
