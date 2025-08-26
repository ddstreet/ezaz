#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK

import argparse
import sys
import traceback

from contextlib import suppress
from functools import cached_property

from .actionutil import ActionConfigGroup


class Main:
    def __init__(self, *, args=sys.argv[1:], cmds=None, venv=None):
        self.args = args
        self.cmds = cmds
        self.venv = venv

    def parse_args(self, args):
        from .argparse import SharedArgumentParser
        parser = SharedArgumentParser(prog='ezaz', formatter_class=argparse.RawTextHelpFormatter)
        parser.add_argument('--venv-verbose', action='store_true', help=argparse.SUPPRESS)
        parser.add_argument('--venv-refresh', action='store_true', help=argparse.SUPPRESS)
        parser.add_argument('--cachedir', shared=True, help='Path to cache directory')
        parser.add_argument('--configfile', shared=True, help='Path to config file')
        parser.add_argument('--trace', shared=True, action='store_true', help='Enable tracing of az commands')
        parser.add_argument('-v', '--verbose', shared=True, action='count', default=0, help='Increase verbosity')
        parser.add_argument('-n', '--dry-run', shared=True, action='store_true',
                            help='Only print what would be done, do not run commands (show/list commands are still run)')

        commands = ActionConfigGroup(action='command',
                                     description='Commands',
                                     required=True,
                                     actionconfigs=[c.get_command_action_config() for c in self.cmds])
        commands.add_to_parser(parser)

        with suppress(ImportError):
            import argcomplete
            argcomplete.autocomplete(parser)

        options = parser.parse_args(args)
        options.full_args = args

        self.setup_logging(verbose=options.verbose, trace=options.trace)

        return options

    @cached_property
    def options(self):
        try:
            return self.parse_args(self.args)
        except Exception as e:
            traceback.print_exc()
            raise

    def setup_logging(self, verbose, trace):
        import logging
        logging.basicConfig(level=logging.NOTSET, format='{message}', style='{')

        from . import LOGGER
        from . import LOG_LEVEL_V0
        from . import LOG_LEVEL_V5
        LOGGER.setLevel(max(LOG_LEVEL_V5, LOG_LEVEL_V0 - verbose))

        from . import AZ_TRACE_LOGGER
        AZ_TRACE_LOGGER.setLevel(logging.NOTSET)
        AZ_TRACE_LOGGER.propagate = trace

    def run(self):
        try:
            self.options.action_function(**vars(self.options))
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
        from . import LOGGER
        from .command import COMMAND_CLASSES
        from .exception import DefaultConfigNotFound
        from .exception import EzazException

        try:
            Main(cmds=COMMAND_CLASSES, venv=venv).run()
            return 0
        except DefaultConfigNotFound as dcnf:
            LOGGER.error(f'ERROR: {dcnf}')
            LOGGER.error("You can set up defaults with 'ezaz setup'")
        except EzazException as e:
            LOGGER.error(f'ERROR ({e.__class__.__name__}): {e}')
        except KeyboardInterrupt:
            LOGGER.error('Aborting.')
        return -1
