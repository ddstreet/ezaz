
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

from ..actionutil import ActionConfig
from ..actionutil import ActionHandler
from ..argutil import ArgConfig
from ..argutil import ArgMap
from ..argutil import ArgUtil
from ..argutil import BoolArgConfig
from ..argutil import ConstArgConfig
from ..argutil import GroupArgConfig
from ..cache import Cache
from ..config import Config
from ..exception import DefaultConfigNotFound
from ..exception import NoActionConfigMethod
from ..exception import NotLoggedIn
from ..exception import RequiredArgument
from ..exception import RequiredArgumentGroup
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

    @classmethod
    def parser_add_argument_verbose(cls, parser):
        return parser.add_argument('-v', '--verbose', action='count', default=0,
                                   help='Be verbose')

    @classmethod
    def parser_add_argument_dry_run(cls, parser):
        return parser.add_argument('-n', '--dry-run', action='store_true',
                                   help='Only print what would be done, do not run commands')

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

    @cached_property
    def verbose(self):
        # Unfortunately, argparse doesn't correctly pass arg values down to subparsers
        verbose_parser = argparse.ArgumentParser(add_help=False)
        self.parser_add_argument_verbose(verbose_parser)
        self.parser_add_argument_dry_run(verbose_parser)
        # Need this so the parser will pick up -v even in combined short params, e.g. -fvn
        verbose_parser.add_argument(*map(lambda a: f'-{a}', re.sub(r'[vVnN]', '', string.ascii_letters)), action='store_true')
        return verbose_parser.parse_known_args(self.options.full_args)[0].verbose

    @cached_property
    def dry_run(self):
        # Unfortunately, argparse doesn't correctly pass arg values down to subparsers
        dry_run_parser = argparse.ArgumentParser(add_help=False)
        self.parser_add_argument_verbose(dry_run_parser)
        self.parser_add_argument_dry_run(dry_run_parser)
        # Need this so the parser will pick up -n even in combined short params, e.g. -fvn
        dry_run_parser.add_argument(*map(lambda a: f'-{a}', re.sub(r'[vVnN]', '', string.ascii_letters)), action='store_true')
        return dry_run_parser.parse_known_args(self.options.full_args)[0].dry_run

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
        cls.parser_add_common_arguments(parser)
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
    def make_action_config(cls, action, *, handler_fn=None, **kwargs):
        return ActionConfig(action,
                            handler=cls.make_action_handler(handler_fn or getattr(cls, cls._arg_to_opt(action))),
                            **kwargs)

    @classmethod
    def make_action_handler(cls, func):
        class CommandClassActionHandler(ActionHandler):
            def __call__(self, command, **opts):
                return self.func(command.parent_command, **opts)

        class CommandObjectActionHandler(ActionHandler):
            def __call__(self, command, **opts):
                return self.func(command, **opts)

        if inspect.ismethod(func):
            return CommandClassActionHandler(func)
        else:
            return CommandObjectActionHandler(func)

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
        config = self.get_action_config(self.action)
        if config:
            return config.handle(command=self, **self.opts)
        raise NoActionConfigMethod()

    def _run(self, **opts):
        # Either implement this, or set up action configs to invoke handler methods
        raise NotImplementedError()

    def run(self):
        try:
            response = self.run_action_config_method()
            if self.verbose:
                response.print_verbose()
            else:
                response.print()
        except NoActionConfigMethod:
            self._run(**self.opts)


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
    def get_azobject_action_configmap(cls):
        return cls.azclass().get_action_configmap()

    @classmethod
    def get_action_configmap(cls):
        return ArgMap(super().get_action_configmap(), cls.get_azobject_action_configmap())

    @classmethod
    def get_default_action(cls):
        return 'show'

    def _run(self, **opts):
        print('CALLING do_action, FIXME')
        return self.azobject.do_action(**opts)


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
        return getattr(self.options, self.azclass().get_self_id_argconfig_dest(is_parent=True), None)

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
        # TODO: this logic should be in the actioncfg
        if not self.is_parent and self.action in ['create', 'delete']:
            raise RequiredArgument(self.azobject_name(), self.action)
        return super().azobject_default_id
