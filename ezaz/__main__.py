#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK

import argparse
import sys

from contextlib import suppress
from functools import cached_property

from .command import COMMAND_CLASSES
from .config import Config
from .exception import DefaultConfigNotFound
from .exception import EzazException
from .importvenv import ImportVenv


class Main:
    def __init__(self, args=sys.argv[1:], venv=None):
        self._args = args
        self._venv = venv

    def parse_args(self, args):
        parser = argparse.ArgumentParser(prog='ezaz')
        parser.add_argument('--venv-refresh',
                            action='store_true',
                            help='Refresh the venv used for package imports')
        parser.add_argument('-v', '--verbose', dest='toplevel_verbose',
                            action='store_true',
                            help='Be verbose')
        parser.add_argument('-n', '--dry-run', dest='toplevel_dry_run',
                            action='store_true',
                            help='Only print what would be done, do not run commands')

        cmds = [c.command_name_short() + (f' ({", ".join(c.aliases())})' if c.aliases() else '')
                for c in COMMAND_CLASSES]
        description = f'Available subcommands (and aliases): {", ".join(cmds)}'
        subparsers = parser.add_subparsers(description=description,
                                           required=True,
                                           metavar='SUBCOMMAND',
                                           help='Subcommand to run')

        for c in COMMAND_CLASSES:
            c.parser_add_subparser(subparsers)

        with suppress(ImportError):
            import argcomplete
            argcomplete.autocomplete(parser)

        options = parser.parse_args(args)

        options.verbose |= options.toplevel_verbose
        options.dry_run |= options.toplevel_dry_run

        return options

    @cached_property
    def options(self):
        return self.parse_args(self._args)

    @cached_property
    def config(self):
        return Config()

    @cached_property
    def command(self):
        return self.options.command_class(self.config, self.options, venv=self._venv)

    def run(self):
        self.command.run()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('--venv-refresh', action='store_true')
    options = parser.parse_known_args(sys.argv[1:])[0]
    with ImportVenv(verbose=options.verbose, clear=options.venv_refresh) as venv:
        try:
            Main(venv=venv).run()
        except DefaultConfigNotFound as dcnf:
            print(f'ERROR: {dcnf}')
            print("You can set up defaults with 'ezaz setup'")
        except EzazException as e:
            print(f'ERROR: {e}')
