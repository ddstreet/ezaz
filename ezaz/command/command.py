
from abc import ABC
from abc import abstractmethod
from contextlib import contextmanager
from types import SimpleNamespace

from ..actionutil import ActionConfig
from ..actionutil import ActionConfigGroup
from ..argutil import ArgUtil
from ..timing import TIMESTAMP


class SimpleCommand(ArgUtil, ABC):
    # For auto-importing
    EZAZ_COMMAND_CLASS = True

    @classmethod
    @abstractmethod
    def command_name_list(cls):
        pass

    @classmethod
    def command_name(cls, sep='_'):
        return sep.join(cls.command_name_list())

    @classmethod
    def command_name_short(cls):
        return cls.command_name('')

    @classmethod
    def command_text(cls):
        return cls.command_name(' ')

    @classmethod
    def command_arg(cls):
        return '--' + cls.command_name('-')

    @classmethod
    def aliases(cls):
        return []

    @classmethod
    def is_command(cls, command):
        return command in [cls.command_name_short(), *cls.aliases()]

    @classmethod
    def command_preparse_args(cls, args):
        return args

    @classmethod
    def get_command_action_config(cls):
        return CommandActionConfig(cls.command_name_short(),
                                   cls,
                                   description='',
                                   aliases=cls.aliases(),
                                   defaults=cls.get_simple_command_defaults(),
                                   parser_kwargs=cls.get_simple_command_parser_kwargs(),
                                   argconfigs=cls.get_simple_command_argconfigs())

    @classmethod
    def get_simple_command_defaults(cls):
        return {}

    @classmethod
    def get_simple_command_parser_kwargs(cls):
        return {}

    @classmethod
    def get_simple_command_argconfigs(cls):
        return []

    def __init__(self, *, verbose=0, dry_run=False, **opts):
        self._verbose = verbose
        self._dry_run = dry_run
        self._opts = opts
        self._indent = 0

    @property
    def opts(self):
        return self._opts

    @property
    def options(self):
        return SimpleNamespace(**self.opts)

    @property
    def verbose(self):
        return self._verbose

    @property
    def dry_run(self):
        return self._dry_run

    @contextmanager
    def indent(self, spaces=2):
        self._indent += spaces
        try:
            yield
        finally:
            self._indent -= spaces

    @property
    def tab(self):
        return ' ' * self._indent


class AzObjectCommand(SimpleCommand):
    @classmethod
    @abstractmethod
    def azclass(cls):
        pass

    @classmethod
    def azobject_name(cls):
        return cls.azclass().azobject_name()

    @classmethod
    def command_name_list(cls):
        return cls.azclass().azobject_name_list()

    @property
    def azobject(self):
        return self.azclass().get_instance(**self.opts)


class ActionCommand(SimpleCommand):
    @classmethod
    def get_command_action_config(cls):
        return ActionConfigGroup(cls.command_name_short(),
                                 description=None,
                                 aliases=cls.aliases(),
                                 default=cls.get_default_action(),
                                 actionconfigs=cls.get_action_configs())

    @classmethod
    def get_action_configs(cls):
        return []

    @classmethod
    def get_action_config(cls, action):
        for config in cls.get_action_configs():
            if config.is_action(action):
                return config
        return None

    @classmethod
    def get_default_action(cls):
        return 'show'

    @classmethod
    def make_action_config(cls, action, **kwargs):
        return CommandActionConfig(action, cls, **kwargs)


class AzObjectActionCommand(AzObjectCommand, ActionCommand):
    @classmethod
    def get_azobject_action_configs(cls):
        return cls.azclass().get_action_configs()

    @classmethod
    def get_action_configs(cls):
        return super().get_action_configs() + cls.get_azobject_action_configs()

    @classmethod
    def make_azaction_config(cls, azactioncfg, **kwargs):
        return AzObjectCommandActionConfig(azactioncfg.action, cls, azactioncfg, **kwargs)



class CommandActionConfig(ActionConfig):
    def __init__(self, action, command_class, *, func=None, **kwargs):
        super().__init__(action, **kwargs)
        self.command_class = command_class
        self.func = func or action

    def _do_action(self, **opts):
        command = self.command_class(**opts)
        do_action = getattr(command, self.func)
        return do_action(**opts)

    def do_action(self, **opts):
        try:
            return self._do_action(**opts)
        finally:
            TIMESTAMP('CommandActionConfig _do_action')

    def cmd_opts(self, **opts):
        return self._args_to_opts(**self.cmd_args(**opts))


class AzObjectCommandActionConfig(CommandActionConfig):
    def __init__(self, action, command_class, azactioncfg, **kwargs):
        kwargs.setdefault('aliases', azactioncfg.aliases)
        kwargs.setdefault('description', azactioncfg.description)
        super().__init__(action, command_class, **kwargs)
        self.azactioncfg = azactioncfg

    @property
    def argconfigs(self):
        return super().argconfigs + self.azactioncfg.argconfigs

    def _do_action(self, **opts):
        return self.azactioncfg.do_action(**opts)
