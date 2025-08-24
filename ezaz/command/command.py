
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
    def parser_register_as_command_subparser(cls, subparsers):
        parser = subparsers.add_parser(cls.command_name_short(), aliases=cls.aliases())
        parser.formatter_class = argparse.RawTextHelpFormatter
        cls.parser_add_arguments(parser)
        parser.set_defaults(command_class=cls)
        cls._parser = parser

    @classmethod
    def parser_add_arguments(cls, parser):
        pass

    def __init__(self, *, options, **kwargs):
        self._options = options

    @property
    def options(self):
        return self._options

    @property
    def opts(self):
        return vars(self.options)

    @property
    def verbose(self):
        return self.options.verbose

    @property
    def dry_run(self):
        return self.options.dry_run

    @abstractmethod
    def run(self):
        pass


class ActionCommand(SimpleCommand):
    @classmethod
    def parser_add_arguments(cls, parser):
        super().parser_add_arguments(parser)
        actions_subparser = cls.parser_create_action_subparser_group(parser)
        cls.parser_add_action_parsers(actions_subparser)

    @classmethod
    def parser_create_action_subparser_group(cls, parser):
        description = '\n'.join(cls.get_action_summaries())
        return parser.add_subparsers(title='Actions',
                                     dest='action',
                                     metavar='',
                                     required=False,
                                     description=description)

    @classmethod
    def parser_add_action_parsers(cls, actions_subparser):
        for config in cls.get_action_configs():
            cls.parser_add_action_parser(actions_subparser, config)

    @classmethod
    def parser_add_action_parser(cls, actions_subparser, config):
        parser = actions_subparser.add_parser(config.action, aliases=config.aliases)
        parser.formatter_class = argparse.RawTextHelpFormatter
        cls.parser_add_action_arguments(parser, config)
        return parser

    @classmethod
    def parser_add_action_arguments(cls, parser, config):
        config.add_to_parser(parser)

    @classmethod
    def get_action_configmap(cls):
        return {}

    @classmethod
    def get_action_names(cls):
        return list(cls.get_action_configmap().keys())

    @classmethod
    def get_action_configs(cls):
        return list(cls.get_action_configmap().values())

    @classmethod
    def get_action_summaries(cls):
        return map(lambda c: c.summary, cls.get_action_configs())

    @classmethod
    def get_action_config(cls, action):
        for config in cls.get_action_configs():
            if config.is_action(action):
                return config
        return None

    @classmethod
    def make_action_config(cls, action, **kwargs):
        return CommandActionConfig(action, cls, **kwargs)

    def get_specified_action(self):
        with suppress(AttributeError):
            return self.get_action_config(self.options.action).action
        return None

    @classmethod
    def get_default_action(cls):
        raise NoDefaultAction()

    @property
    def action(self):
        return self._arg_to_opt(self.get_specified_action() or self.get_default_action())

    def run_action_config_method(self):
        config = self.get_action_config(self.action)
        if config:
            return config.do_action(**self.opts)
        raise NoActionConfigMethod(f'ActionConfig missing for action {self.action}')

    def run(self):
        try:
            result = self.run_action_config_method()
            if isinstance(result, list):
                for r in result:
                    LOG_V0(r)
            elif result:
                LOG_V0(result)
        except NoDefaultAction:
            self._parser.print_help()


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
    def get_azobject_action_configmap(cls):
        return cls.azclass().get_action_configmap()

    @classmethod
    def get_action_configmap(cls):
        return ArgMap(super().get_action_configmap(), cls.get_azobject_action_configmap())

    @classmethod
    def get_default_action(cls):
        return 'show'


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
        return getattr(self.options, self.azclass().get_self_id_argconfig_dest(is_parent=self.is_parent), None)

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
    @property
    def azobject_default_id(self):
        if not self.is_parent and self.action in ['create', 'delete']:
            raise RequiredArgument(self.azobject_name(), self.action)
        return super().azobject_default_id


class CommandActionConfig(ActionConfig):
    def __init__(self, action, command_class, **kwargs):
        super().__init__(action, **kwargs)
        self.command_class = command_class

    def do_action(self, **opts):
        command = self.command_class(options=SimpleNamespace(opts))
        do_action = getattr(command, self.action)
        do_action(**opts)
