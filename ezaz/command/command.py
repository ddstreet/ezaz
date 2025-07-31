
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

from ..argutil import ArgConfig
from ..argutil import ArgUtil
from ..cache import Cache
from ..config import Config
from ..exception import DefaultConfigNotFound
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
    def parser_add_argument_azobject_id(cls, parser, is_parent=False):
        if cls.parent_command_cls().is_azsubcommand():
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


class ActionCommand(SimpleCommand):
    @classmethod
    def parser_add_arguments(cls, parser):
        super().parser_add_arguments(parser)
        actions_subparser = cls.parser_create_action_subparser_group(parser)
        cls.parser_add_action_parsers(actions_subparser)

    @classmethod
    def parser_create_action_subparser_group(cls, parser):
        description = '\n'.join(cls.parser_get_action_descriptions())
        return parser.add_subparsers(title='Actions',
                                     dest='action',
                                     metavar='',
                                     required=False,
                                     description=description)

    @classmethod
    def parser_add_action_parsers(cls, actions_subparser):
        for config in cls.parser_get_action_configs():
            cls.parser_add_action_parser(actions_subparser, config)

    @classmethod
    def parser_add_action_parser(cls, actions_subparser, config):
        parser = actions_subparser.add_parser(config.name, aliases=config.aliases)
        parser._action_config = config
        parser.formatter_class = argparse.RawTextHelpFormatter
        cls.parser_add_common_arguments(parser)
        with suppress(AttributeError):
            getattr(cls, f'parser_add_{config.name}_action_arguments')(parser)
        return parser

    @classmethod
    @abstractmethod
    def parser_get_action_names(cls):
        return []

    @classmethod
    def parser_get_action_configs(cls):
        for name in cls.parser_get_action_names():
            yield getattr(cls, f'parser_get_{cls._arg_to_name(name)}_action_config')()

    @classmethod
    def parser_get_action_descriptions(cls):
        for config in cls.parser_get_action_configs():
            yield config.description

    def parser_get_specified_action(self):
        return self._parser_get_action_parser_name_for_alias(self.options.action)

    @classmethod
    @abstractmethod
    def parser_get_default_action(cls):
        pass

    @classmethod
    def _parser_get_action_config(cls, parser):
        return getattr(parser, '_action_config', None)

    @classmethod
    def _parser_is_action_config_name(cls, config, name):
        return (name in [config.name, *config.aliases] if config else False)

    @classmethod
    def _parser_is_action_parser_name(cls, parser, name):
        return cls._parser_is_action_config_name(cls._parser_get_action_config(parser), name)

    @classmethod
    def _parser_get_action_parser_name_for_alias(cls, name_or_alias):
        for config in cls.parser_get_action_configs():
            if cls._parser_is_action_config_name(config, name_or_alias):
                return config.name
        return None

    @property
    def action(self):
        return (self.parser_get_specified_action() or self.parser_get_default_action()).replace('-', '_')

    def do_show(self):
        # TODO: move all showy-stuff into command class
        self.azobject.show()

    def run(self):
        try:
            return getattr(self, f'do_{self.action}')()
        except AttributeError:
            return self.azobject.do_action(action=self.action, opts=vars(self.options))


class CreateActionCommand(ActionCommand, AzObjectCommand):
    @classmethod
    def parser_get_action_names(cls):
        return super().parser_get_action_names() + ['create']

    @classmethod
    def parser_get_create_action_config(cls):
        return ArgConfig('create', description=cls.parser_get_create_action_description())

    @classmethod
    def parser_get_create_action_description(cls):
        return f'Create a {cls.command_text()}'

    @property
    def azobject_default_id(self):
        if self.action == 'create' and not self.is_parent:
            raise RequiredArgument(self.azobject_name(), 'create')
        return super().azobject_default_id


class DeleteActionCommand(ActionCommand, AzObjectCommand):
    @classmethod
    def parser_get_action_names(cls):
        return super().parser_get_action_names() + ['delete']

    @classmethod
    def parser_get_delete_action_config(cls):
        return ArgConfig('delete', description=cls.parser_get_delete_action_description())

    @classmethod
    def parser_get_delete_action_description(cls):
        return f'Delete a {cls.command_text()}'

    @property
    def azobject_default_id(self):
        if self.action == 'delete' and not self.is_parent:
            raise RequiredArgument(self.azobject_name(), 'delete')
        return super().azobject_default_id


class ListActionCommand(ActionCommand, AzSubCommand):
    @classmethod
    def parser_get_action_names(cls):
        return super().parser_get_action_names() + ['list']

    @classmethod
    def parser_get_list_action_config(cls):
        return ArgConfig('list', description=cls.parser_get_list_action_description())

    @classmethod
    def parser_get_list_action_description(cls):
        return f'List {cls.command_text()}s'

    @classmethod
    def _parser_add_argument_azobject_id(cls, parser, is_parent):
        # Don't add our own object id param, as the list command lists them all
        if is_parent or not cls._parser_is_action_parser_name(parser, 'list'):
            super()._parser_add_argument_azobject_id(parser, is_parent)

    @classmethod
    def parser_add_list_action_arguments(cls, parser):
        parser.add_argument('--filter-prefix',
                            help=f'In addition to configured filters, also filter {cls.command_text()}s that start with the prefix')
        parser.add_argument('--filter-suffix',
                            help=f'In addition to configured filters, also filter {cls.command_text()}s that end with the suffix')
        parser.add_argument('--filter-regex',
                            help=f'In addition to configured filters, also filter {cls.command_text()}s that match the regular expression')
        parser.add_argument('-N', '--no-filters', action='store_true',
                            help=f'Do not use any configured filters (the --filter-* parameters will still be used)')

    def do_list(self):
        self.azclass.list(self.parent_azobject, **vars(self.options))


class ShowActionCommand(ActionCommand, AzObjectCommand):
    @classmethod
    def parser_get_action_names(cls):
        return super().parser_get_action_names() + ['show']

    @classmethod
    def parser_get_show_action_config(cls):
        return ArgConfig('show', description=cls.parser_get_show_action_description())

    @classmethod
    def parser_get_show_action_description(cls):
        return f'Show default {cls.command_text()} (default)'

    @classmethod
    def parser_get_default_action(cls):
        return 'show'


class SetActionCommand(ActionCommand, AzSubCommand):
    @classmethod
    def parser_get_action_names(cls):
        return super().parser_get_action_names() + ['set']

    @classmethod
    def parser_get_set_action_config(cls):
        return ArgConfig('set', description=cls.parser_get_set_action_description())

    @classmethod
    def parser_get_set_action_description(cls):
        return f'Set default {cls.command_text()}'

    def set(self):
        if self.action != 'set':
            super().run()
        self.azobject.set_default(**vars(self.options))


class ClearActionCommand(ActionCommand, AzSubCommand):
    @classmethod
    def parser_get_action_names(cls):
        return super().parser_get_action_names() + ['clear']

    @classmethod
    def parser_get_clear_action_config(cls):
        return ArgConfig('clear', description=cls.parser_get_clear_action_description())

    @classmethod
    def parser_get_clear_action_description(cls):
        return f'Clear default {cls.command_text()}'

    def run(self):
        if self.action == 'clear':
            self.azobject.clear_default(**vars(self.options))
        else:
            super().run()


class FilterActionCommand(ActionCommand, AzObjectCommand):
    @classmethod
    def parser_get_action_names(cls):
        return (super().parser_get_action_names() +
                (['filter'] if cls.azobject_class().is_azsubobject_container() else []))

    @classmethod
    def parser_get_filter_action_config(cls):
        return ArgConfig('filter', description=cls.parser_get_filter_action_description())

    @classmethod
    def parser_get_filter_action_description(cls):
        return f'Edit filtering for {cls.command_text()}'

    @classmethod
    def parser_add_filter_action_arguments(cls, parser):
        filter_type_group = parser.add_mutually_exclusive_group()
        filter_type_group.add_argument('--filter-all',
                                       action='store_const',
                                       dest='filter_type',
                                       const=FILTER_ALL,
                                       help=f'Add/update/show a filter for all object types (use with caution)')
        for azobject_cls in cls.azobject_class().get_azsubobject_descendants():
            filter_type_group.add_argument(f'--filter-{azobject_cls.azobject_name("-")}',
                                           action='store_const',
                                           dest='filter_type',
                                           const=azobject_cls.azobject_name(),
                                           help=f'Add/update/show a filter for {azobject_cls.azobject_text()}s')
        filter_type_group.add_argument('--filter-default',
                                       action='store_const',
                                       dest='filter_type',
                                       const=FILTER_DEFAULT,
                                       help=f'Add/update/show a default filter (use with caution)')

        prefix_group = parser.add_mutually_exclusive_group()
        prefix_group.add_argument('--prefix',
                                  help=f'Filter object names that start with the prefix')
        prefix_group.add_argument('--no-prefix', dest='prefix', action='store_const', const='',
                                  help=f'Remove prefix filter')

        suffix_group = parser.add_mutually_exclusive_group()
        suffix_group.add_argument('--suffix',
                                  help=f'Filter object names that end with the suffix')
        suffix_group.add_argument('--no-suffix', dest='suffix', action='store_const', const='',
                                  help=f'Remove suffix filter')

        regex_group = parser.add_mutually_exclusive_group()
        regex_group.add_argument('--regex',
                                 help=f'Filter object names that match the regular expression')
        regex_group.add_argument('--no-regex', dest='regex', action='store_const', const='',
                                 help=f'Remove regex filter')

        parser.add_argument('--show-parent-filters', action='store_true',
                            help='Also show our parent object(s) filters')

    @classmethod
    def _filter_types(cls):
        return (['filter_all'] +
                [f'filter_{azobject_cls.azobject_name()}' for azobject_cls in
                 cls.azobject_class().get_azsubobject_descendants()] +
                ['filter_default'])

    def _filter_action_items(self):
        for k in ['prefix', 'suffix', 'regex']:
            v = getattr(self.options, k, None)
            if v is not None:
                yield k, v

    def _filter_check_args(self):
        for k, v in self._filter_action_items():
            if not self.options.filter_type:
                raise RequiredArgumentGroup(self._filter_types(), f'--{k}', exclusive=True)

    def _filter_update(self):
        for k, v in self._filter_action_items():
            setattr(self.azobject.filters.get_filter(self.options.filter_type), k, v)

    def _filter_show(self):
        print(self.azobject.filters)

    def run(self):
        if self.action == 'filter':
            self._filter_check_args()
            self._filter_update()
            self._filter_show()
        else:
            super().run()


class RoActionCommand(
        ListActionCommand,
        ShowActionCommand,
        SetActionCommand,
        ClearActionCommand,
        FilterActionCommand,
): pass


class RwActionCommand(
        CreateActionCommand,
        DeleteActionCommand,
): pass


class CommonActionCommand(
        RoActionCommand,
        RwActionCommand,
): pass


class UploadActionCommand(CreateActionCommand):
    @classmethod
    def parser_get_create_action_config(cls):
        return ArgConfig('create', aliases=['upload'], description=cls.parser_get_create_action_description())


class DownloadActionCommand(ActionCommand, AzObjectCommand):
    @classmethod
    def parser_get_action_names(cls):
        return super().parser_get_action_names() + ['download']

    @classmethod
    def parser_get_download_action_config(cls):
        return ArgConfig('download', description=cls.parser_get_download_action_description())

    @classmethod
    def parser_get_download_action_description(cls):
        return f'Download a {cls.command_text()}'


class AllActionCommand(
        CommonActionCommand,
        UploadActionCommand,
        DownloadActionCommand,
): pass
