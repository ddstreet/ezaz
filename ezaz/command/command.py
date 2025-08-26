
import argcomplete
import argparse
import inspect
import json
import os
import re
import string
import subprocess

from abc import ABC
from abc import abstractmethod
from contextlib import contextmanager
from contextlib import suppress
from functools import cached_property
from types import SimpleNamespace

from .. import LOG_V0
from ..actionutil import ActionConfig
from ..actionutil import ActionConfigGroup
from ..argutil import ArgConfig
from ..argutil import ArgMap
from ..argutil import ArgUtil
from ..argutil import BoolArgConfig
from ..argutil import ConstArgConfig
from ..argutil import GroupArgConfig
from ..exception import NoActionConfigMethod
from ..exception import NoDefaultAction
from ..exception import NotLoggedIn
from ..exception import RequiredArgument
from ..exception import RequiredArgumentGroup


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
    def get_command_action_config(cls):
        return CommandActionConfig(cls.command_name_short(),
                                   cls,
                                   description='',
                                   aliases=cls.aliases(),
                                   argconfigs=cls.get_simple_command_argconfigs())

    @classmethod
    def get_simple_command_argconfigs(cls):
        return []

    def __init__(self, *, verbose=0, dry_run=False, **opts):
        self._verbose = verbose
        self._dry_run = dry_run
        self._opts = opts

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

    @classmethod
    def make_azaction_config(cls, azactioncfg, **kwargs):
        return AzObjectCommandActionConfig(azactioncfg.action, cls, azactioncfg, **kwargs)


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

    @cached_property
    def azobject(self):
        return self.azclass().get_instance(**self.opts)


class AzObjectActionCommand(AzObjectCommand, ActionCommand):
    @classmethod
    def get_azobject_action_configs(cls):
        return cls.azclass().get_action_configs()

    @classmethod
    def get_action_configs(cls):
        return super().get_action_configs() + cls.get_azobject_action_configs()


class AzSubObjectCommand(AzObjectCommand):
    @classmethod
    @abstractmethod
    def parent_command_cls(cls):
        pass

    def __init__(self, *, is_parent=False, **kwargs):
        super().__init__(**kwargs)
        self._is_parent = is_parent
        self._parent_command = self.parent_command_cls()(is_parent=True, **kwargs)
        assert isinstance(self._parent_command, AzObjectCommand)

    @property
    def is_parent(self):
        return self._is_parent

    @property
    def parent_command(self):
        return self._parent_command

    @property
    def parent_azobject(self):
        return self.parent_command.azobject

    @property
    def azobject_specified_id(self):
        return self.opts.get(self.azclass().azobject_name())

    @property
    def azobject_default_id(self):
        return self.parent_azobject.get_default_child_id(self.azobject_name())

    @property
    def azobject_id(self):
        return self.azobject_specified_id or self.azobject_default_id

    @cached_property
    def azobject(self):
        return self.parent_azobject.get_child(self.azobject_name(), self.azobject_id)


class AzSubObjectActionCommand(AzSubObjectCommand, AzObjectActionCommand):
    pass


class AzDefaultable(AzSubObjectCommand):
    @classmethod
    def get_action_configs(cls):
        return [*super().get_action_configs(),
                cls.make_action_config('default',
                                       description=f'Configure the default {cls.azclass().azobject_text()}',
                                       argconfigs=cls.get_default_action_argconfigs())]

    @classmethod
    def get_default_action_argconfigs(cls):
        return [GroupArgConfig(ConstArgConfig('s', 'set', const='default_set', help='Set the default'),
                               ConstArgConfig('u', 'unset', const='default_unset', help='Unset the default'),
                               ConstArgConfig('show', const='default_show', help='Show the default, if any (default)'),
                               cmddest='default_action')]

    @classmethod
    def default(cls, parent, **opts):
        default_action = cls.get_default_action_config().cmd_args(**opts).get('default_action')
        if default_action:
            return getattr(cls, default_action)(parent, **opts)

    @classmethod
    def default_set(cls, parent, **opts):
        default_id = cls.required_arg_value(cls.azobject_name(), opts, '--set')
        parent.set_default_child_id(cls.azobject_name(), default_id)
        return f'Set default {cls.azobject_text()}: {default_id}'

    @classmethod
    def default_unset(cls, parent, **opts):
        parent.del_default_child_id(cls.azobject_name())
        return f'Unset default {cls.azobject_text()}'

    @classmethod
    def default_show(cls, parent, **opts):
        return f'Default {cls.azobject_text()}: {parent.get_default_child_id(cls.azobject_name())}'


class AzFilterer(AzObjectCommand):
    @classmethod
    def get_action_configs(cls):
        return super().get_action_configs() + ([cls.get_filter_action_config()] if cls.azclass().has_child_classes() else [])

    @classmethod
    def get_filter_action_config(cls):
        return ActionConfigGroup('filter',
                                 description=f"Configure the filters for this {cls.azclass().azobject_text()}'s descendant objects",
                                 actionconfigs=[cls.make_action_config('set', description='Set filters'),
                                                cls.make_action_config('get', description='Get filters'),
                                                cls.make_action_config('unset', description='Unset/remove filters')])

    @classmethod
    def get_filter_action_argconfigs(cls):
        return [GroupArgConfig(ArgConfig('--prefix', help=f'Update filter to select only object names that start with the prefix'),
                               ConstArgConfig('--no-prefix', dest='prefix', const='', help=f'Remove prefix filter')),
                GroupArgConfig(ArgConfig('--suffix', help=f'Update filter to select only object names that end with the suffix'),
                               ConstArgConfig('--no-suffix', dest='suffix', const='', help=f'Remove suffix filter')),
                GroupArgConfig(ArgConfig('--regex', help=f'Update filter to select only object names that match the regular expression'),
                               ConstArgConfig('--no-regex', dest='regex', const='', help=f'Remove regex filter')),
                GroupArgConfig(*[ConstArgConfig(azclass.azobject_name(),
                                                const=azclass.azobject_name(),
                                                dest='filter_type',
                                                help=f'Configure a filter for {azclass.azobject_text()}s')
                                 for azclass in cls.azclass().get_descendant_classes()])]

    def filter(self, filter_type=None, prefix=None, suffix=None, regex=None, **opts):
        print('filter called')
        return ''
        if not filter_type:
            raise RequiredArgumentGroup(self.get_filter_type_groupargconfig().opts, self._opt_to_arg(ftype), exclusive=True)
        setattr(self.filters.get_filter(filter_type), ftype, opts.get(ftype))
        return str(self.filters)


class CommandActionConfig(ActionConfig):
    def __init__(self, action, command_class, **kwargs):
        super().__init__(action, **kwargs)
        self.command_class = command_class

    def _do_action(self, **opts):
        command = self.command_class(**opts)
        do_action = getattr(command, self.action)
        return do_action()

    def do_action(self, **opts):
        result = self._do_action(**opts)
        if isinstance(result, list):
            for r in result:
                LOG_V0(r)
        elif result:
            LOG_V0(result)

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
