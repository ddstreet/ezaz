
import argparse

from abc import ABC
from abc import abstractmethod

from .argutil import ArgMap
from .argutil import ArgUtil
from .exception import ArgumentError


class ActionConfig(ArgUtil, ABC):
    def __init__(self, action, description, *, aliases=None, argconfigs=None):
        self.action = action
        self.aliases = aliases or []
        self.description = description
        self._argconfigs = argconfigs
        self.parser = None
        self.group_default = False
        self.common_parsers = []

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

    @abstractmethod
    def do_action(self, **opts):
        pass

    def add_to_group(self, group):
        assert self.parser is None
        self.parser = group.add_parser(self.action, aliases=self.aliases, parents=self.common_parsers)
        self.parser.formatter_class = argparse.RawTextHelpFormatter
        self.parser.set_defaults(action_function=self.do_action)
        for argconfig in self.argconfigs:
            argconfig.add_to_parser(self.parser)
        return self.parser

    def cmd_args(self, **opts):
        return ArgMap(*map(lambda argconfig: argconfig.cmd_args(**opts), self.argconfigs))


class ActionConfigGroup(ActionConfig):
    def __init__(self, action, description, *, aliases=None, default=None, required=False, actionconfigs=None, common_parsers=None):
        super().__init__(action, description, aliases=aliases)
        self.required = required
        self.actionconfigs = actionconfigs or []
        self.common_parsers = common_parsers or []
        self.group = None
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
        return self.default_actionconfig.argconfigs if self.default_actionconfig else []

    @property
    def group_description(self):
        return '\n'.join(sorted(map(str, self.actionconfigs)))

    def add_to_group(self, group):
        self.add_to_parser(super().add_to_group(group))

    def add_to_parser(self, parser):
        assert self.group is None
        self.group = parser.add_subparsers(title='Actions',
                                           description=self.group_description,
                                           required=self.required,
                                           metavar='')
        for actionconfig in self.actionconfigs:
            # The actionconfig is created before passing it to us, so
            # we have to update it here instead of in the actionconfig
            # constructor. This works for normal ActionConfigs as well
            # as sub-ActionConfigGroups.
            actionconfig.common_parsers += self.common_parsers
            actionconfig.add_to_group(self.group)

    def do_action(self, **opts):
        if self.default_actionconfig:
            self.default_actionconfig.do_action(**opts)
        else:
            self.parser.print_help()

    def cmd_args(self, **opts):
        if self.default_actionconfig:
            return self.default_actionconfig.cmd_args(**opts)
        else:
            raise RuntimeError('No default, cannot provide cmd_args')
