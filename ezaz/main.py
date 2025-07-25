#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK

import argparse
import sys
import traceback

from contextlib import suppress
from functools import cached_property

from .argparse import SharedArgumentParser


class Main:
    def __init__(self, *, args=sys.argv[1:], cmds=None, venv=None):
        self.args = args
        self.cmds = cmds
        self.venv = venv

    def _subcmd_description(self, subcmd):
        return (subcmd.command_name_short() +
                (f' ({",".join(subcmd.aliases())})' if subcmd.aliases() else ''))

    @property
    def subcmds_description(self):
        return '\n'.join([self._subcmd_description(c)
                          for c in sorted(self.cmds, key=lambda c: c.command_name_short())])

    def parse_args(self, args):
        parser = SharedArgumentParser(prog='ezaz', formatter_class=argparse.RawTextHelpFormatter)
        parser.add_argument('--venv-verbose', action='store_true', help=argparse.SUPPRESS)
        parser.add_argument('--venv-refresh', action='store_true', help=argparse.SUPPRESS)
        parser.add_argument('--cachedir', shared=True, help='Path to cache directory')
        parser.add_argument('--configfile', shared=True, help='Path to config file')
        parser.add_argument('-v', '--verbose',
                            shared=True,
                            action='count',
                            default=0,
                            help='Be verbose')
        parser.add_argument('-n', '--dry-run',
                            shared=True,
                            action='store_true',
                            help='Only print what would be done, do not run commands')

        subparsers = parser.add_subparsers(title='Subcommands (and aliases)',
                                           description=self.subcmds_description,
                                           required=True,
                                           metavar='')

        for c in self.cmds:
            c.parser_register_as_command_subparser(subparsers)

        with suppress(ImportError):
            import argcomplete
            argcomplete.autocomplete(parser)

        options = parser.parse_args(args)
        options.full_args = args

        return options

    @cached_property
    def options(self):
        try:
            return self.parse_args(self.args)
        except Exception as e:
            traceback.print_exc()
            raise

    @cached_property
    def command(self):
        return self.options.command_class(options=self.options)

    def run(self):
        try:
            self.command.run()
        except Exception as e:
            if self.options.verbose > 1:
                traceback.print_exc()
            raise


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
            return 0
        except DefaultConfigNotFound as dcnf:
            print(f'ERROR: {dcnf}')
            print("You can set up defaults with 'ezaz setup'")
        except EzazException as e:
            print(f'ERROR ({e.__class__.__name__}): {e}')
        except KeyboardInterrupt:
            print('Aborting.')
        return -1
