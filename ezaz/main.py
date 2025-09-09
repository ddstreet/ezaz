#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK

import argparse
import sys
import traceback

from contextlib import suppress
from functools import cached_property

from .actionutil import ActionConfigGroup
from .argutil import SharedArgumentParser
from .timing import TIMESTAMP


class Main:
    def __init__(self, *, args=sys.argv[1:], cmds=None, venv=None, shared_args=None):
        self.args = args
        self.cmds = cmds
        self.venv = venv
        self.shared_args = shared_args or []
        self._options = None

    def setup_logging(self, options):
        import logging
        logging.basicConfig(level={0: logging.WARNING, 1: logging.INFO, 2: logging.DEBUG}.get(options.verbose, logging.DEBUG),
                            format='{message}', style='{')

        from . import IMPORTCLASSES_LOGGER
        IMPORTCLASSES_LOGGER.propagate = options.debug_importclasses
        IMPORTCLASSES_LOGGER.setLevel(logging.NOTSET)

        from . import AZ_LOGGER
        AZ_LOGGER.setLevel({0: logging.CRITICAL, 1: logging.INFO, 2: logging.DEBUG}.get(options.debug_az, logging.DEBUG))

        from . import LOGGER
        LOGGER.setLevel(logging.NOTSET)

    @cached_property
    def shared_argument_parser(self):
        parser = SharedArgumentParser(all_shared=True, shared_args=self.shared_args, add_help=False)
        group = parser.add_shared_argument_group(title='Global options')
        group.add_argument('--debug-parser', action='store_true', help=argparse.SUPPRESS)
        group.add_argument('--debug-importclasses', action='store_true', help=argparse.SUPPRESS)
        group.add_argument('--debug-az', action='count', default=0, help='Enable debug of az commands')
        group.add_argument('--no-cache', action='store_true', help='Use no cached data (do update the cache)')
        group.add_argument('--cachedir', metavar='PATH', help='Path to cache directory')
        group.add_argument('--configfile', metavar='PATH', help='Path to config file')
        group.add_argument('-v', '--verbose', action='count', default=0, help='Increase verbosity')
        group.add_argument('-n', '--dry-run', action='store_true',
                           help='For commands other than show/list, only print what would be done, do not run commands')
        return parser

    def get_command(self, args):
        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument('command', nargs='?')
        command = parser.parse_known_args(args)[0].command
        if command:
            for cmd in self.cmds:
                if cmd.is_command(command):
                    return cmd
        return None

    def autocomplete(self, parser):
        with suppress(ImportError):
            import argcomplete
            argcomplete.autocomplete(parser)

    def parse_args(self, args):
        self.setup_logging(self.shared_argument_parser.parse_known_args(self.args)[0])

        # Speed up; just add the command arguments we need
        # Helps especially with argcomplete
        command = self.get_command(args)
        if command:
            args = command.command_preparse_args(args)

        group = ActionConfigGroup(action='command',
                                  description='Commands',
                                  required=True,
                                  actionconfigs=([command.get_command_action_config()]
                                                 if command else
                                                 [c.get_command_action_config() for c in self.cmds]))

        parser = SharedArgumentParser(prog='ezaz',
                                      formatter_class=argparse.RawTextHelpFormatter,
                                      shared_args=self.shared_argument_parser.shared_args)
        group.add_to_parser(parser)

        self.autocomplete(parser)

        options = parser.parse_args(args)
        options.full_args = args

        if options.debug_parser:
            for k, v in vars(options).items():
                print(f'{k}: {v}')
            sys.exit(1)

        TIMESTAMP('main.parse_args()')
        return options

    @property
    def options(self):
        if not self._options:
            self._options = self.parse_args(self.args)
        return self._options

    def run(self):
        try:
            self.options.action_function(**vars(self.options))
        except Exception:
            if not self._options or self.options.verbose > 1:
                traceback.print_exc()
            raise


def main():
    TIMESTAMP('start main()')
    parser = SharedArgumentParser(all_shared=True, add_help=False)
    parser.add_argument('--debug-timing', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--debug-venv', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--no-venv', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--refresh-venv', action='store_true', help=argparse.SUPPRESS)
    options = parser.parse_known_args(sys.argv[1:])[0]

    from .importvenv import ImportVenv
    with ImportVenv(debug=options.debug_venv, refresh=options.refresh_venv, no_venv=options.no_venv) as venv:
        from . import LOGGER
        from .command import COMMAND_CLASSES
        from .exception import DefaultConfigNotFound
        from .exception import EzazException

        try:
            Main(cmds=COMMAND_CLASSES, venv=venv, shared_args=parser.shared_args).run()
            return 0
        except DefaultConfigNotFound as dcnf:
            LOGGER.error(f'ERROR: {dcnf}')
            LOGGER.error("You can set up defaults with 'ezaz setup'")
        except EzazException as e:
            LOGGER.error(f'ERROR ({e.__class__.__name__}): {e}')
        except KeyboardInterrupt:
            LOGGER.error('Aborting.')
        finally:
            if options.debug_timing:
                TIMESTAMP.show()

        return -1
