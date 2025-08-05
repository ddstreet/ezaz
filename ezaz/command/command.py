
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
        return getattr(self.options, self.azobject_name(), None)

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

    # TODO - re-implement list filtering...
    def __parser_get_list_action_builtin_args(cls):
        return [ArgConfig('--filter-prefix',
                          help=f'In addition to configured filters, also filter {cls.command_text()}s that start with the prefix'),
                ArgConfig('--filter-suffix',
                          help=f'In addition to configured filters, also filter {cls.command_text()}s that end with the suffix'),
                ArgConfig('--filter-regex',
                          help=f'In addition to configured filters, also filter {cls.command_text()}s that match the regular expression'),
                BoolArgConfig('-N', '--no-filters',
                          help=f'Do not use any configured filters (the --filter-* parameters will still be used)')]


# TODO - re-implement filter configuration
class FilterActionCommand: #ActionCommand, AzObjectCommand):
    @classmethod
    def parser_get_action_builtin_names(cls):
        return (super().parser_get_action_builtin_names() +
                (['filter'] if cls.azclass().is_child_container() else []))

    @classmethod
    def parser_get_filter_action_builtin_config(cls):
        return cls.make_action_config('filter',
                                      aliases=cls.parser_get_filter_action_builtin_aliases(),
                                      description=cls.parser_get_filter_action_builtin_description(),
                                      argconfigs=cls.parser_get_filter_action_builtin_args())

    @classmethod
    def parser_get_filter_action_builtin_aliases(cls):
        return []

    @classmethod
    def parser_get_filter_action_builtin_description(cls):
        return f'Edit filtering for {cls.command_text()}'

    @classmethod
    def _parser_filter_type(cls):
        filter_all = ConstArgConfig('--filter-all', dest='filter_type', const=FILTER_ALL,
                                    help=f'Add/update/show a filter for all object types (use with caution)')
        filter_azobjects = [ConstArgConfig(f'--filter-{azobject_cls.azobject_name("-")}', dest='filter_type',
                                           const=azobject_cls.azobject_name(),
                                           help=f'Add/update/show a filter for {azobject_cls.azobject_text()}s')
                            for azobject_cls in cls.azclass().get_descendants()]
        filter_default = ConstArgConfig('--filter-default', dest='filter_type', const=FILTER_DEFAULT,
                                        help=f'Add/update/show a default filter (use with caution)')
        return GroupArgConfig(filter_all, *filter_azobjects, filter_default)

    @classmethod
    def _parser_filter_actions(cls):
        return [GroupArgConfig(ArgConfig('--prefix', help=f'Filter object names that start with the prefix'),
                               ConstArgConfig('--no-prefix', dest='prefix', const='', help=f'Remove prefix filter')),
                GroupArgConfig(ArgConfig('--suffix', help=f'Filter object names that end with the suffix'),
                               ConstArgConfig('--no-suffix', dest='suffix', const='', help=f'Remove suffix filter')),
                GroupArgConfig(ArgConfig('--regex', help=f'Filter object names that match the regular expression'),
                               ConstArgConfig('--no-regex', dest='regex', const='', help=f'Remove regex filter'))]

    @classmethod
    def parser_get_filter_action_builtin_args(cls):
        return [cls._parser_filter_type(), *cls._parser_filter_actions()]

    def _filter_update(self):
        for k, v in ArgMap(*[arg.action_args(self.options) for arg in self._parser_filter_actions()]).items():
            if self.options.filter_type:
                setattr(self.azobject.filters.get_filter(self.options.filter_type), k, v)
            else:
                raise RequiredArgumentGroup(self._parser_filter_type().opts, k, exclusive=True)

    def _filter_show(self):
        print(self.azobject.filters)

    def run(self):
        if self.action == 'filter':
            self._filter_update()
            self._filter_show()
        else:
            super().run()

