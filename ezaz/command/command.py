
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

from ..cache import Cache
from ..config import Config
from ..exception import DefaultConfigNotFound
from ..exception import NotLoggedIn
from ..exception import RequiredArgument
from ..response import lookup_response


class SimpleCommand(ABC):
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
        parser.add_argument('--debug-argcomplete', action='store_true', help=argparse.SUPPRESS)
        cls.parser_add_argument_verbose(parser)
        cls.parser_add_argument_dry_run(parser)

    @classmethod
    def parser_add_argument_verbose(cls, parser):
        return parser.add_argument('-v', '--verbose', action='store_true',
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
    def config(self):
        return self._config

    @property
    def cache(self):
        return self._cache

    @property
    def verbose(self):
        return self._options.verbose

    @property
    def dry_run(self):
        return self._options.dry_run

    @abstractmethod
    def run(self):
        pass


class ActionParser:
    def __init__(self, name, aliases=[], description=None):
        self.name = name
        self.aliases = aliases
        self.description = description


class ActionCommand(SimpleCommand):
    @classmethod
    def parser_add_arguments(cls, parser):
        super().parser_add_arguments(parser)
        actions = cls.parser_create_action_subparser_group(parser)
        cls.parser_add_action_parsers(actions)

    @classmethod
    def parser_create_action_subparser_group(cls, parser):
        description = '\n'.join(cls.parser_get_action_descriptions())
        return parser.add_subparsers(title='Actions',
                                     dest='action',
                                     metavar='',
                                     required=False,
                                     description=description)

    @classmethod
    def parser_add_action_parsers(cls, actions):
        for parser in cls.parser_get_action_parsers():
            cls._parser_add_action_parser(actions, parser)

    @classmethod
    def _parser_add_action_parser(cls, actions, action_parser):
        parser = actions.add_parser(action_parser.name, aliases=action_parser.aliases)
        parser.formatter_class = argparse.RawTextHelpFormatter
        cls.parser_add_common_arguments(parser)
        with suppress(AttributeError):
            getattr(cls, f'parser_add_{action_parser.name}_action_arguments')(parser)
        return parser

    @classmethod
    def parser_get_action_descriptions(cls):
        for parser in cls.parser_get_action_parsers():
            if parser.description:
                yield f'{parser.name}: {parser.description}'

    @classmethod
    @abstractmethod
    def parser_get_action_parsers(cls):
        return []

    @classmethod
    @abstractmethod
    def parser_get_action_default(cls):
        pass

    def _run(self):
        action = self._options.action or self.parser_get_action_default()
        getattr(self, action.replace('-', '_'))()

    def run(self):
        try:
            self._run()
        except NotLoggedIn as nli:
            print(str(nli))


class AzObjectCommand(SimpleCommand):
    @classmethod
    @abstractmethod
    def azobject_class(cls):
        pass

    @classmethod
    def azobject_name(cls):
        return cls.azobject_class().azobject_name()

    @classmethod
    def command_name_list(cls):
        return cls.azobject_class().azobject_name_list()

    @classmethod
    def is_azsubcommand(cls):
        return False

    @cached_property
    def azobject(self):
        return self.azobject_class()(config=self.config, cache=self.cache, verbose=self.verbose, dry_run=self.dry_run)


class AzSubCommand(AzObjectCommand):
    @classmethod
    @abstractmethod
    def parent_command_cls(cls):
        pass

    @classmethod
    def is_azsubcommand(cls):
        return True

    @classmethod
    def parser_add_common_arguments(cls, parser):
        super().parser_add_common_arguments(parser)
        cls.parser_add_argument_azobject_id(parser)

    @classmethod
    def parser_add_argument_azobject_id(cls, parser):
        if cls.parent_command_cls().is_azsubcommand():
            cls.parent_command_cls().parser_add_argument_azobject_id(parser)
        arg = parser.add_argument(f'--{cls.command_name("-")}',
                                  help=f'Use the specified {cls.command_text()}, instead of the default')
        arg.completer = cls.completer_azobject_ids
        return arg

    @classmethod
    def completer_info_attrs(cls, *, completer_attr=None, parsed_args={}, **kwargs):
        try:
            options = parsed_args
            options.action = 'argcomplete'
            parent = cls.parent_command_cls()(options=options, cache=Cache(), config=Config(), is_parent=True)
            return [getattr(info, completer_attr) if completer_attr else cls.azobject_class().info_id(info)
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
    def azclass(self):
        return self.parent_azobject.get_azsubobject_class(self.azobject_name())

    @property
    def azobject_specified_id(self):
        return getattr(self._options, self.azobject_name(), None)

    @property
    def azobject_default_id(self):
        return self.parent_azobject.get_azsubobject_default_id(self.azobject_name())

    @property
    def azobject_id(self):
        return self.azobject_specified_id or self.azobject_default_id

    @cached_property
    def azobject(self):
        return self.parent_azobject.get_azsubobject(self.azobject_name(), self.azobject_id)


class ShowActionCommand(ActionCommand, AzObjectCommand):
    @classmethod
    def parser_get_action_parsers(cls):
        return (super().parser_get_action_parsers() +
                [ActionParser('show', description=cls.parser_get_show_action_description())])

    @classmethod
    def parser_get_show_action_description(cls):
        return f'Show default {cls.command_text()} (default)'

    @classmethod
    def parser_get_action_default(cls):
        return 'show'

    def show(self):
        self.azobject.show()


class CreateActionCommand(ActionCommand, AzObjectCommand):
    @classmethod
    def parser_get_action_parsers(cls):
        return (super().parser_get_action_parsers() +
                [ActionParser('create', description=cls.parser_get_create_action_description())])

    @classmethod
    def parser_get_create_action_description(cls):
        return f'Create a {cls.command_text()}'

    @property
    def azobject_default_id(self):
        if self._options.action == 'create' and not self.is_parent:
            raise RequiredArgument(self.azobject_name(), 'create')
        return super().azobject_default_id

    def create(self):
        self.azobject.create(**vars(self._options))


class DeleteActionCommand(ActionCommand, AzObjectCommand):
    @classmethod
    def parser_get_action_parsers(cls):
        return (super().parser_get_action_parsers() +
                [ActionParser('delete', description=cls.parser_get_delete_action_description())])

    @classmethod
    def parser_get_delete_action_description(cls):
        return f'Delete a {cls.command_text()}'

    def delete(self):
        self.azobject.delete(**vars(self._options))


class ListActionCommand(ActionCommand, AzSubCommand):
    @classmethod
    def parser_get_action_parsers(cls):
        return (super().parser_get_action_parsers() +
                [ActionParser('list', description=cls.parser_get_list_action_description())])

    @classmethod
    def parser_get_list_action_description(cls):
        return f'List {cls.command_text()}s'

    def list(self):
        self.azclass.list(self.parent_azobject, **vars(self._options))


class SetActionCommand(ActionCommand, AzSubCommand):
    @classmethod
    def parser_get_action_parsers(cls):
        return (super().parser_get_action_parsers() +
                [ActionParser('set', description=cls.parser_get_set_action_description())])

    @classmethod
    def parser_get_set_action_description(cls):
        return f'Set default {cls.command_text()}'

    def set(self):
        self.azobject.set_default(**vars(self._options))


class ClearActionCommand(ActionCommand, AzSubCommand):
    @classmethod
    def parser_get_action_parsers(cls):
        return (super().parser_get_action_parsers() +
                [ActionParser('clear', description=cls.parser_get_clear_action_description())])

    @classmethod
    def parser_get_clear_action_description(cls):
        return f'Clear default {cls.command_text()}'

    def clear(self):
        self.azobject.clear_default(**vars(self._options))


class FilterActionCommand(ActionCommand, AzSubCommand):
    @classmethod
    def parser_get_action_parsers(cls):
        return (super().parser_get_action_parsers() +
                [ActionParser('filter', description=cls.parser_get_filter_action_description())])

    @classmethod
    def parser_get_filter_action_description(cls):
        return f'Edit filtering for {cls.command_text()}'

    @classmethod
    def parser_add_filter_action_arguments(cls, parser):
        enable_group = parser.add_mutually_exclusive_group()
        enable_group.add_argument('--enable', action='store_true',
                                  help=f'Enable {cls.command_text()} filtering')
        enable_group.add_argument('--disable', action='store_true',
                                  help=f'Disable {cls.command_text()} filtering')

        prefix_group = parser.add_mutually_exclusive_group()
        prefix_group.add_argument('--prefix',
                                  help=f'Filter {cls.command_text()}s that start with the prefix')
        prefix_group.add_argument('--no-prefix', dest='prefix', action='store_const', const='',
                                  help=f'Do not filter {cls.command_text()}s by prefix')

        suffix_group = parser.add_mutually_exclusive_group()
        suffix_group.add_argument('--suffix',
                                  help=f'Filter {cls.command_text()}s that end with the suffix')
        suffix_group.add_argument('--no-suffix', dest='suffix', action='store_const', const='',
                                  help=f'Do not filter {cls.command_text()}s by suffix')

        regex_group = parser.add_mutually_exclusive_group()
        regex_group.add_argument('--regex',
                                 help=f'Filter {cls.command_text()}s that match the regular expression')
        regex_group.add_argument('--no-regex', dest='regex', action='store_const', const='',
                                 help=f'Do not filter {cls.command_text()}s by regex')

    def filter(self):
        azfilter = self.azobject.filter

        for f in ['prefix', 'suffix', 'regex']:
            v = getattr(self._options, f)
            if v is not None:
                getattr(azfilter, f'set_{f}')(v)

        if self._options.enable:
            azfilter.enable()
        if self._options.disable:
            azfilter.disable()

        print(azfilter)


class AllActionCommand(FilterActionCommand, CreateActionCommand, DeleteActionCommand, SetActionCommand, ClearActionCommand, ListActionCommand, ShowActionCommand):
    pass
