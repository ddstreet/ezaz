
import argcomplete
import argparse
import json
import os
import subprocess

from abc import ABC
from abc import abstractmethod
from contextlib import contextmanager
from contextlib import suppress
from functools import cached_property
from types import SimpleNamespace

from ..argutil import ActionConfig
from ..argutil import ArgConfig
from ..argutil import ArgMap
from ..argutil import ArgUtil
from ..argutil import BoolArgConfig
from ..argutil import ConstArgConfig
from ..argutil import GroupArgConfig
from ..argutil import noop
from ..cache import Cache
from ..config import Config
from ..exception import DefaultConfigNotFound
from ..exception import NoActionConfigMethod
from ..exception import NotLoggedIn
from ..exception import RequiredArgument
from ..exception import RequiredArgumentGroup
from ..filter import FILTER_ALL
from ..filter import FILTER_DEFAULT
from ..response import lookup_response


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

    @classmethod
    def parser_add_arguments(cls, parser):
        cls.parser_add_common_arguments(parser)

    @classmethod
    def parser_add_common_arguments(cls, parser):
        cls.parser_add_argument_verbose(parser)
        cls.parser_add_argument_dry_run(parser)
        cls.parser_add_common_hidden_arguments(parser)

    @classmethod
    def parser_add_argument_verbose(cls, parser):
        return parser.add_argument('-v', '--verbose', action='store_true',
                                   help='Be verbose')

    @classmethod
    def parser_add_argument_dry_run(cls, parser):
        return parser.add_argument('-n', '--dry-run', action='store_true',
                                   help='Only print what would be done, do not run commands')

    @classmethod
    def parser_add_common_hidden_arguments(cls, parser):
        parser.add_argument('--debug-argcomplete', action='store_true', help=argparse.SUPPRESS)

    def __init__(self, *, options, config, cache=None, **kwargs):
        self._options = options
        self._config = config
        self._cache = cache

    @property
    def options(self):
        return self._options

    @property
    def opts(self):
        return vars(self.options)

    @property
    def config(self):
        return self._config

    @property
    def cache(self):
        return self._cache

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
        parser._action_config = config
        parser.formatter_class = argparse.RawTextHelpFormatter
        cls.parser_add_action_arguments(parser, config)
        return parser

    @classmethod
    def parser_add_action_arguments(cls, parser, config):
        cls.parser_add_common_arguments(parser)
        for argconfig in config.argconfigs:
            argconfig.add_to_parser(parser)

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

    def get_specified_action(self):
        with suppress(AttributeError):
            return self.get_action_config(self.options.action).action
        return None

    @classmethod
    @abstractmethod
    def get_default_action(cls):
        pass

    @property
    def action(self):
        return self._arg_to_opt(self.get_specified_action() or self.get_default_action())

    def run_action_config_method(self):
        cmdobjmethod = self.get_action_config(self.action).cmdobjmethod
        if cmdobjmethod:
            return getattr(self, cmdobjmethod)(action=self.action, opts=self.opts)
        raise NoActionConfigMethod()

    @abstractmethod
    def _run(self, action, opts):
        pass

    def run(self):
        with suppress(NoActionConfigMethod):
            return self.run_action_config_method()
        return self._run(action=self.action, opts=self.opts)


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
        return self.azclass()(config=self.config, cache=self.cache, verbose=self.verbose, dry_run=self.dry_run)


class AzObjectActionCommand(AzObjectCommand, ActionCommand):
    @classmethod
    def parser_add_action_arguments(cls, parser, config):
        cls.parser_add_argument_azobject_id(parser)
        super().parser_add_action_arguments(parser, config)

    @classmethod
    def parser_add_argument_azobject_id(cls, parser, is_parent=False):
        # Only sub-objects have multiple instances, so don't add id argument for non-sub-objects
        pass

    @classmethod
    def get_azobject_action_configmap(cls):
        return cls.azclass().get_action_configmap()

    @classmethod
    def get_action_configmap(cls):
        return ArgMap(super().get_action_configmap(), cls.get_azobject_action_configmap())

    @classmethod
    def get_default_action(cls):
        return 'show'

    def run_action_config_method(self):
        with suppress(NoActionConfigMethod):
            return super().run_action_config_method()
        azobjmethod = self.get_action_config(self.action).azobjmethod
        if azobjmethod:
            return getattr(self.azobject, azobjmethod)(action=self.action, opts=self.opts)
        raise NoActionConfigMethod()

    def _run(self, action, opts):
        return self.azobject.do_action(action=action, opts=opts)


class AzSubObjectCommand(AzObjectCommand):
    @classmethod
    @abstractmethod
    def parent_command_cls(cls):
        pass

    @classmethod
    def parser_add_argument_azobject_id(cls, parser, is_parent=False):
        cls.parent_command_cls().parser_add_argument_azobject_id(parser, is_parent=True)
        cls._parser_add_argument_azobject_id(parser, is_parent)

    @classmethod
    def _parser_add_argument_azobject_id(cls, parser, is_parent):
        parser.add_argument(f'{cls.command_arg()}',
                            help=f'Use the specified {cls.command_text()}, instead of the default').completer = cls.completer_azobject_ids

    @classmethod
    def completer_info_attrs(cls, *, completer_attr=None, parsed_args={}, **kwargs):
        try:
            options = parsed_args
            options.action = 'argcomplete'
            parent = cls.parent_command_cls()(options=options, cache=Cache(), config=Config(), is_parent=True)
            return [getattr(info, completer_attr) if completer_attr else cls.azclass().info_id(info)
                    for info in parent.azobject.get_azsubobject_infos(cls.azobject_name())]
        except Exception as e:
            if getattr(parsed_args, 'debug_argcomplete', True):
                argcomplete.warn(f'argcomplete error: {e}')
            raise

    @classmethod
    def completer_names(cls, **kwargs):
        return cls.completer_info_attrs(completer_attr='name', **kwargs)

    @classmethod
    def completer_azobject_ids(cls, **kwargs):
        return cls.completer_info_attrs(completer_attr=None, **kwargs)

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
        return getattr(self.options, self.azobject_name(), None)

    @property
    def azobject_default_id(self):
        return self.parent_azobject.get_azsubobject_default_id(self.azobject_name())

    @property
    def azobject_id(self):
        return self.azobject_specified_id or self.azobject_default_id

    @cached_property
    def azobject(self):
        return self.parent_azobject.get_azsubobject(self.azobject_name(), self.azobject_id)


class AzSubObjectActionCommand(AzSubObjectCommand, AzObjectActionCommand):
    def run_action_config_method(self):
        with suppress(NoActionConfigMethod):
            return super().run_action_config_method()
        cmdclsmethod = self.get_action_config(self.action).cmdclsmethod
        if cmdclsmethod:
            return getattr(self, cmdclsmethod)(action=self.action, opts=self.opts, parent=self.parent_command)
        azclsmethod = self.get_action_config(self.action).azclsmethod
        if azclsmethod:
            return getattr(self.azobject, azclsmethod)(action=self.action, opts=self.opts, parent=self.parent_azobject)
        raise NoActionConfigMethod()
