#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK

import argparse
import sys

from contextlib import suppress
from functools import cached_property


class Main:
    def __init__(self, *, args=sys.argv[1:], cmds=None, venv=None):
        self.args = args
        self.cmds = cmds
        self.venv = venv

    def _cmd_aliases(self, cmd):
        return ', '.join(cmd.aliases())

    def _subcmd_name_and_aliases(self, cmd):
        return f'{c.command_name_short()}{aliases}'

    def parse_args(self, args):
        parser = argparse.ArgumentParser(prog='ezaz', formatter_class=argparse.RawTextHelpFormatter)
        parser.add_argument('--venv-verbose', action='store_true', help=argparse.SUPPRESS)
        parser.add_argument('--venv-refresh', action='store_true', help=argparse.SUPPRESS)
        parser.add_argument('-v', '--verbose', dest='toplevel_verbose',
                            action='store_true',
                            help='Be verbose')
        parser.add_argument('-n', '--dry-run', dest='toplevel_dry_run',
                            action='store_true',
                            help='Only print what would be done, do not run commands')

        description = 'Available subcommands (and aliases):\n'
        for c in sorted(self.cmds, key=lambda c: c.command_name_short()):
            description += f'  {c.command_name_short()}'
            if c.aliases():
                description += f' ({",".join(c.aliases())})'
            description += '\n'
        subparsers = parser.add_subparsers(description=description,
                                           required=True,
                                           metavar='')

        for c in self.cmds:
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
        return self.parse_args(self.args)

    @cached_property
    def config(self):
        from .config import Config
        return Config()

    @cached_property
    def command(self):
        return self.options.command_class(self.config, self.options, venv=self.venv)

    def run(self):
        self.command.run()


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--venv-verbose', action='store_true')
    parser.add_argument('--venv-refresh', action='store_true')
    options = parser.parse_known_args(sys.argv[1:])[0]

    from .importvenv import ImportVenv
    with ImportVenv(verbose=options.venv_verbose, refresh=options.venv_refresh) as venv:
        from .command import COMMAND_CLASSES
        from .exception import DefaultConfigNotFound
        from .exception import EzazException

        try:
            Main(cmds=COMMAND_CLASSES, venv=venv).run()
        except DefaultConfigNotFound as dcnf:
            print(f'ERROR: {dcnf}')
            print("You can set up defaults with 'ezaz setup'")
        except EzazException as e:
            print(f'ERROR: {e}')
