
from abc import ABC
from abc import abstractmethod

from .argutil import ArgMap
from .argutil import ArgUtil


class ActionConfig(ArgUtil, ABC):
    def __init__(self, action, *, aliases=[], description='', argconfigs=[]):
        self.action = action
        self.aliases = aliases
        self.description = description
        self.argconfigs = argconfigs

    @abstractmethod
    def do_action(self, **opts):
        pass

    def is_action(self, action):
        return action in ([self.action] + self.aliases)

    @property
    def summary(self):
        s = self.action
        if self.aliases:
            s += f' ({",".join(self.aliases)})'
        if self.description:
            s += f': {self.description}'
        return s

    def add_to_parser(self, parser):
        for argconfig in self.argconfigs:
            argconfig.add_to_parser(parser)

    def cmd_args(self, **opts):
        return ArgMap(*map(lambda argconfig: argconfig.cmd_args(**opts), self.argconfigs))

    def get_arg_value(self, arg, **opts):
        opt = self._arg_to_opt(arg)
        return self.cmd_args(**{opt: opts.get(opt)}).get(self._opt_to_arg(opt))
