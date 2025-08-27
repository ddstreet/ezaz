#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK

import argparse
import sys
import traceback

from contextlib import suppress

from .actionutil import ActionConfigGroup


class Main:
    def __init__(self, *, args=sys.argv[1:], cmds=None, venv=None, parent_parser=None):
        self.args = args
        self.cmds = cmds
        self.venv = venv
        self.parent_parser = parent_parser
        self._options = None

    def setup_logging(self, options):
        import logging
        logging.basicConfig(level=logging.NOTSET, format='{message}', style='{')

        from . import IMPORTCLASSES_LOGGER
        IMPORTCLASSES_LOGGER.propagate = options.debug_importclasses
        IMPORTCLASSES_LOGGER.setLevel(logging.NOTSET)

        from . import AZ_LOGGER
        AZ_LOGGER.propagate = options.debug_az
        AZ_LOGGER.setLevel({0: logging.INFO, 1: logging.INFO, 2: logging.DEBUG}.get(options.verbose, logging.NOTSET))

        from . import LOGGER
        LOGGER.setLevel({0: logging.WARNING, 1: logging.INFO, 2: logging.DEBUG}.get(options.verbose, logging.NOTSET))

    def parse_args(self, args):
        common_parser = argparse.ArgumentParser(add_help=False)
        common_parser.add_argument('--cachedir', help='Path to cache directory')
        common_parser.add_argument('--configfile', help='Path to config file')
        common_parser.add_argument('--debug-az', action='store_true', help='Enable debug of az commands')
        common_parser.add_argument('--debug-importclasses', action='store_true', help=argparse.SUPPRESS)
        common_parser.add_argument('-v', '--verbose', action='count', default=0, help='Increase verbosity')
        common_parser.add_argument('-n', '--dry-run', action='store_true',
                                   help='Only print what would be done, do not run commands (show/list commands are still run)')

        common_options = common_parser.parse_known_args(self.args)[0]
        self.setup_logging(common_options)

        from .argparse import SharedArgumentParser
        parser = SharedArgumentParser(prog='ezaz',
                                      formatter_class=argparse.RawTextHelpFormatter,
                                      parents=[self.parent_parser, common_parser])

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

        self.finished_parsing_options = True
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
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--debug-venv', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--refresh-venv', action='store_true', help=argparse.SUPPRESS)
    options = parser.parse_known_args(sys.argv[1:])[0]

    from .importvenv import ImportVenv
    with ImportVenv(debug=options.debug_venv, refresh=options.refresh_venv) as venv:
        from . import LOGGER
        from .command import COMMAND_CLASSES
        from .exception import DefaultConfigNotFound
        from .exception import EzazException

        try:
            Main(cmds=COMMAND_CLASSES, venv=venv, parent_parser=parser).run()
            return 0
        except DefaultConfigNotFound as dcnf:
            LOGGER.error(f'ERROR: {dcnf}')
            LOGGER.error("You can set up defaults with 'ezaz setup'")
        except EzazException as e:
            LOGGER.error(f'ERROR ({e.__class__.__name__}): {e}')
        except KeyboardInterrupt:
            LOGGER.error('Aborting.')
        return -1
