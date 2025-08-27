
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
from ..exception import DefaultConfigNotFound
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


class AzDefaultable(AzObjectActionCommand):
    @classmethod
    def get_action_configs(cls):
        return [*super().get_action_configs(),
                cls.get_default_action_config()]

    @classmethod
    def get_default_action_config(cls):
        return ActionConfigGroup('default',
                                 description=f'Configure the default {cls.azclass().azobject_text()}',
                                 actionconfigs=[cls.get_default_set_action_config(),
                                                cls.get_default_unset_action_config(),
                                                cls.get_default_get_action_config()])

    @classmethod
    def get_default_set_action_config(cls):
        return cls.make_action_config('set',
                                      func='set_default',
                                      description='Set default',
                                      argconfigs=[*cls.azclass().get_self_id_argconfig(help='Default {cls.azclass().azobject_text()} id to set'),
                                                  BoolArgConfig('force', help='Set the default even if the object does not exist')])

    @classmethod
    def get_default_unset_action_config(cls):
        return cls.make_action_config('unset',
                                      func='unset_default',
                                      description='Unset default',
                                      argconfigs=[])

    @classmethod
    def get_default_get_action_config(cls):
        return cls.make_action_config('get',
                                      func='get_default',
                                      description='Get/show default',
                                      argconfigs=[])

    def set_default(self, force=False, **opts):
        name = self.azclass().azobject_name()
        text = self.azclass().azobject_text()
        azobject = self.azclass().get_specified_instance(**opts)

        try:
            old_default_id = azobject.parent.get_default_child_id(name)
        except DefaultConfigNotFound:
            old_default_id = None

        if old_default_id == azobject.azobject_id:
            return f'Default {text} is already: {old_default_id}'

        new_obj_text = f'{text}: {azobject.azobject_id}'

        if not azobject.exists:
            new_obj_text = f'nonexistent {new_obj_text}'
            if not force:
                return f'Refusing to set {new_obj_text}'

        azobject.parent.set_default_child_id(name, azobject.azobject_id)

        if old_default_id:
            return f'Replaced default {text}: {old_default_id} with {new_obj_text}'

        return f'Set default {new_obj_text}'

    def unset_default(self, **opts):
        name = self.azclass().azobject_name()
        text = self.azclass().azobject_text()

        with suppress(DefaultConfigNotFound):
            parent = self.azobject.parent
            default_id = parent.get_default_child_id(name)
            parent.del_default_child_id(name)
            return f'Removed default {text}: {default_id}'
        return 'No default'

    def get_default(self, **opts):
        with suppress(DefaultConfigNotFound):
            return self.azobject.parent.get_default_child_id(self.azobject.azobject_name())
        return 'No default'


class AzFilterer(AzObjectActionCommand):
    @classmethod
    def get_action_configs(cls):
        return [*super().get_action_configs(), *([cls.get_filter_action_config()]
                                                 if cls.azclass().has_child_classes()
                                                 else [])]

    @classmethod
    def get_filter_action_config(cls):
        return ActionConfigGroup('filter',
                                 description=f"Configure the filters for this {cls.azclass().azobject_text()}'s descendant objects",
                                 actionconfigs=[cls.get_filter_get_action_config(),
                                                cls.get_filter_set_action_config()])

    @classmethod
    def get_filter_set_action_config(cls):
        return cls.make_action_config('set',
                                      func='set_filter',
                                      description='Set filters',
                                      argconfigs=cls.get_filter_action_argconfigs())

    @classmethod
    def get_filter_get_action_config(cls):
        return cls.make_action_config('get',
                                      func='get_filter',
                                      description='Get/show filters',
                                      argconfigs=[])

    @classmethod
    def get_filter_action_argconfigs(cls):
        return [GroupArgConfig(ArgConfig('--prefix', help=f'Update filter to select only object names that start with the prefix'),
                               ConstArgConfig('--no-prefix', dest='prefix', const='', help=f'Remove prefix filter')),
                GroupArgConfig(ArgConfig('--suffix', help=f'Update filter to select only object names that end with the suffix'),
                               ConstArgConfig('--no-suffix', dest='suffix', const='', help=f'Remove suffix filter')),
                GroupArgConfig(ArgConfig('--regex', help=f'Update filter to select only object names that match the regular expression'),
                               ConstArgConfig('--no-regex', dest='regex', const='', help=f'Remove regex filter')),
                cls.get_filter_action_filter_type_argconfigs()]

    @classmethod
    def get_filter_action_filter_type_argconfigs(cls):
        return GroupArgConfig(*[ConstArgConfig(azclass.azobject_name(),
                                               const=azclass.azobject_name(),
                                               dest='filter_type',
                                               help=f'Configure a filter for {azclass.azobject_text()}s')
                                for azclass in cls.azclass().get_descendant_classes()],
                              required=True)

    def _set_filter(self, ftype, fvalue, filter_type):
        if fvalue is None:
            return

        if not filter_type:
            raise RequiredArgumentGroup(self.get_filter_action_filter_type_argconfigs().opts,
                                        self._opt_to_arg(ftype),
                                        exclusive=True)

        setattr(self.azobject.filters.get_filter(filter_type), ftype, fvalue)

    def set_filter(self, filter_type=None, **opts):
        for ftype in ['prefix', 'suffix', 'regex']:
            self._set_filter(ftype, opts.get(ftype), filter_type)
        if filter_type:
            return str(self.azobject.filters.get_filter(filter_type))
        else:
            return self.get_filter(**opts)

    def get_filter(self, **opts):
        return str(self.azobject.filters)


class AzCommonActionCommand(AzFilterer, AzDefaultable, AzObjectActionCommand):
    pass


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
