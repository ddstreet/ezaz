
import argparse

from abc import ABC
from abc import abstractmethod

from . import IS_ARGCOMPLETE
from .argutil import ArgMap
from .argutil import ArgUtil
from .exception import ArgumentError
from .timing import TIMESTAMP


class ActionConfig(ArgUtil, ABC):
    def __init__(self, action, description, *, aliases=None, argconfigs=None, defaults=None, parser_kwargs=None):
        self.action = action
        self.aliases = aliases or []
        self.description = description
        self._argconfigs = argconfigs
        self.defaults = defaults or {}
        self.parser_kwargs = parser_kwargs or {}
        self.group_default = False

    def __str__(self):
        return (self.action +
                (f' ({",".join(self.aliases)})' if self.aliases else '') +
                (f': {self.description}' if self.description else '') +
                (f' (default)' if self.group_default else ''))

    def is_action(self, action):
        return action in ([self.action] + self.aliases)

    @property
    def argconfigs(self):
        return self._argconfigs or []

    def _get_argconfig(self, argconfigs, optname, want_group=False):
        for argconfig in argconfigs:
            if optname in argconfig.opts:
                if not argconfig.is_group or want_group:
                    return argconfig
                else:
                    return self._get_argconfig(argconfig.argconfigs, optname)
        return None

    def get_argconfig(self, optname, want_group=False):
        return self._get_argconfig(self.argconfigs, optname, want_group)

    @abstractmethod
    def do_action(self, **opts):
        pass

    def set_defaults(self, parser):
        parser.set_defaults(action_function=self.do_action, print_help=parser.print_help, **self.defaults)

    def add_to_group(self, group):
        parser = group.add_parser(self.action, aliases=self.aliases, **self.parser_kwargs)
        parser.formatter_class = argparse.RawTextHelpFormatter
        self.set_defaults(parser)
        for argconfig in self.argconfigs:
            argconfig.add_to_parser(parser)
        return parser

    def cmd_args(self, **opts):
        return ArgMap(*map(lambda argconfig: argconfig.cmd_args(**opts), self.argconfigs))


class ActionConfigGroup(ActionConfig):
    def __init__(self, action, description, *, aliases=None, default=None, required=False, actionconfigs=None):
        super().__init__(action, description, aliases=aliases)
        self.required = required
        self.actionconfigs = actionconfigs or []
        self.default_actionconfig = None

        if default:
            for actionconfig in self.actionconfigs:
                if actionconfig.is_action(default):
                    self.default_actionconfig = actionconfig
                    self.default_actionconfig.group_default = True
                    break
            else:
                raise ArgumentError(f'ActionConfig group {action} missing default action {default}')

    @property
    def argconfigs(self):
        if not self.default_actionconfig:
            return []

        for argconfig in self.default_actionconfig.argconfigs:
            if argconfig.required:
                raise ArgumentError(f'Default ActionConfig {self.default_actionconfig.action} has required argument {argconfig.parser_argname}')

        return self.default_actionconfig.argconfigs

    @property
    def group_description(self):
        return '\n'.join(sorted(map(str, self.actionconfigs)))

    def add_to_group(self, group):
        self.add_to_parser(super().add_to_group(group))

    def add_to_parser(self, parser):
        group = parser.add_subparsers(title='Actions',
                                      description=self.group_description,
                                      required=self.required,
                                      metavar='')
        for actionconfig in self.actionconfigs:
            actionconfig.add_to_group(group)
            if IS_ARGCOMPLETE:
                # This timing is really only useful for argcomplete
                TIMESTAMP(f'{self.__class__.__name__}.add_to_group: {actionconfig.action}')

    def do_action(self, **opts):
        if self.default_actionconfig:
            self.default_actionconfig.do_action(**opts)
        else:
            print_help = opts.get('print_help')
            assert print_help
            print_help()

    def cmd_args(self, **opts):
        if self.default_actionconfig:
            return self.default_actionconfig.cmd_args(**opts)
        else:
            raise RuntimeError('No default, cannot provide cmd_args')
