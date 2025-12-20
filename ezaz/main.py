#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK

import argparse
import sys
import traceback

from contextlib import suppress
from functools import cached_property

from . import IS_ARGCOMPLETE
from . import ARGCOMPLETE_ARGS
from .actionutil import ActionConfigGroup
from .argutil import SharedArgumentParser
from .timing import TIMESTAMP


class Main:
    def __init__(self, *, cmds=None, venv=None, shared_args=None):
        self.cmds = cmds
        self.venv = venv
        self.shared_args = shared_args or []
        self._options = None

    @cached_property
    def args(self):
        return ARGCOMPLETE_ARGS[1:] if IS_ARGCOMPLETE else sys.argv[1:]

    def autocomplete(self, parser):
        with suppress(ImportError):
            import argcomplete
            argcomplete.autocomplete(parser, print_suppressed=True, default_completer=None)

    def parse_early_args(self):
        parser = SharedArgumentParser(add_help=False)
        self.parser_add_general_arguments(parser)
        parser.add_argument('command', nargs='?')
        options = parser.parse_known_args(self.args)[0]

        self.command = next((cmd for cmd in self.cmds if cmd.is_command(options.command)), None)

        from .config import Config
        Config.set_global_config(options.configfile)

        if IS_ARGCOMPLETE:
            # argcomplete does not use any logging
            return

        verbose = options.verbose
        debug_importclasses = getattr(options, 'debug_importclasses', False)
        debug_az = getattr(options, 'debug_az', 0)

        import logging
        logging.basicConfig(level={0: logging.WARNING, 1: logging.INFO, 2: logging.DEBUG}.get(verbose, logging.DEBUG),
                            format='{message}', style='{')

        from . import IMPORTCLASSES_LOGGER
        IMPORTCLASSES_LOGGER.propagate = debug_importclasses
        IMPORTCLASSES_LOGGER.setLevel(logging.NOTSET)

        from . import AZ_LOGGER
        AZ_LOGGER.setLevel({0: logging.CRITICAL, 1: logging.INFO, 2: logging.DEBUG}.get(debug_az, logging.DEBUG))

        from . import LOGGER
        LOGGER.setLevel(logging.NOTSET)

    def parser_add_general_arguments(self, parser, add_help=False):
        group = parser.add_shared_argument_group(title='General options')
        if add_help:
            group.add_argument('-h', '--help', action='help', default=argparse.SUPPRESS, help='Show this help message and exit')
        group.add_argument('-v', '--verbose', action='count', default=0, help='Increase verbosity')
        group.add_argument('-n', '--dry-run', action='store_true', help='For commands other than show/list, do not run commands')
        group.add_argument('--debug-parser', action='store_true', default=argparse.SUPPRESS, help=argparse.SUPPRESS)
        group.add_argument('--debug-importclasses', action='store_true', default=argparse.SUPPRESS, help=argparse.SUPPRESS)
        group.add_argument('--debug-az', action='count', default=argparse.SUPPRESS, help='Enable debug of az commands (once to show cmds, twice to show response)')
        group.add_argument('--no-cache', action='store_true', help='Use no cached data (but still update the cache)')
        group.add_argument('--cachedir', metavar='PATH', help='Path to cache directory')

        from .config import Config
        Config.add_argument_to_parser(group, '-C', '--configfile', metavar='PATH')

    @property
    def general_parser(self):
        general_parser = SharedArgumentParser(all_shared=True, shared_args=self.shared_args, add_help=False)
        self.parser_add_general_arguments(general_parser, add_help=True)
        TIMESTAMP('general_parser')
        return general_parser

    def parse_args(self):
        self.parse_early_args()

        # Speed up: add only the command arguments we need. Can save
        # ~0.5 second, which is especially important for argcomplete,
        # but also speeds up fully cached operations
        if self.command:
            args = self.command.command_preparse_args(self.args)
            actionconfigs=[self.command.get_command_action_config()]
        else:
            args = self.args
            actionconfigs=[c.get_command_action_config() for c in self.cmds]

        group = ActionConfigGroup(action='command', description='Commands', required=True, actionconfigs=actionconfigs)
        parser = SharedArgumentParser(prog='ezaz',
                                      add_help=False,
                                      formatter_class=argparse.RawTextHelpFormatter,
                                      shared_args=self.general_parser.shared_args)
        group.add_to_parser(parser)
        TIMESTAMP('parser')

        self.autocomplete(parser)

        options = parser.parse_args(args)
        options.full_args = args

        if getattr(options, 'debug_parser', False):
            for k, v in vars(options).items():
                print(f'{k}: {v}')
            sys.exit(1)

        TIMESTAMP('main.parse_args()')
        return options

    @property
    def options(self):
        if not self._options:
            self._options = self.parse_args()
        return self._options

    def print_result(self, result):
        if isinstance(result, list) and self.options.verbose < 3:
            for r in result:
                print(r)
        elif result:
            print(result)

    def run(self):
        try:
            self.print_result(self.options.action_function(**vars(self.options)))
        except Exception:
            if not self._options or self.options.verbose > 1:
                traceback.print_exc()
            raise


def main():
    TIMESTAMP('start main()')
    parser = SharedArgumentParser(all_shared=True, add_help=False)
    parser.add_argument('--debug-argcomplete', action='store_true', default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    parser.add_argument('--debug-timing', action='store_true', default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    parser.add_argument('--debug-venv', action='store_true', default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    parser.add_argument('--no-venv', action='store_true', default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    parser.add_argument('--refresh-venv', action='store_true', default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    options = parser.parse_known_args(sys.argv[1:])[0]
    debug_venv = getattr(options, 'debug_venv', False)
    refresh_venv = getattr(options, 'refresh_venv', False)
    no_venv = getattr(options, 'no_venv', False)
    debug_timing = getattr(options, 'debug_timing', False)

    from .importvenv import ImportVenv
    with ImportVenv(debug=debug_venv, refresh=refresh_venv, no_venv=no_venv) as venv:
        from . import LOGGER
        from .command import COMMAND_CLASSES
        from .exception import DefaultConfigNotFound
        from .exception import EzazException
        from .exception import TooLongForArgcomplete

        try:
            Main(cmds=COMMAND_CLASSES, venv=venv, shared_args=parser.shared_args).run()
            return 0
        except TooLongForArgcomplete as tlfa:
            import argcomplete
            argcomplete.warn(str(tlfa))
        except DefaultConfigNotFound as dcnf:
            LOGGER.error(f'ERROR: {dcnf}')
            LOGGER.error("You can set up defaults with 'ezaz setup'")
        except EzazException as e:
            LOGGER.error(f'ERROR ({e.__class__.__name__}): {e}')
        except KeyboardInterrupt:
            LOGGER.error('Aborting.')
        finally:
            if debug_timing:
                TIMESTAMP.show()

        return -1
