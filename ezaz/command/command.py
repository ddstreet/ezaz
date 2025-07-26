
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
    def parser_add_subparser(cls, subparsers):
        parser = subparsers.add_parser(cls.command_name_short(), aliases=cls.aliases())
        cls.parser_add_arguments(parser)
        parser.set_defaults(command_class=cls)
        return parser

    @classmethod
    def parser_add_arguments(cls, parser):
        cls.parser_add_common_arguments(parser)

    @classmethod
    def parser_add_common_arguments(cls, parser):
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


class CommandArgumentAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        namespace.command_action = self.option_strings[-1].lstrip('-')
        namespace.command_action_arguments = values


class ActionCommand(SimpleCommand):
    @classmethod
    def parser_add_arguments(cls, parser):
        super().parser_add_arguments(parser)

        group = cls.parser_add_action_group(parser)
        cls.parser_add_action_arguments(group)
        cls.parser_set_action_default(group)

    @classmethod
    def parser_add_action_group(cls, parser):
        title_group = parser.add_argument_group('Action', 'Action to perform')
        return title_group.add_mutually_exclusive_group()

    @classmethod
    @abstractmethod
    def parser_add_action_arguments(cls, group):
        pass

    @classmethod
    def command_metavar(cls):
        return cls.command_name_list()[-1].upper()

    @classmethod
    def _parser_add_action_argument(cls, group, *args, nargs=0, help=None):
        return group.add_argument(*args, action=CommandArgumentAction, dest=None, nargs=nargs, metavar=cls.command_metavar(), help=help)

    @classmethod
    @abstractmethod
    def parser_set_action_default(cls, group):
        pass

    @classmethod
    def _parser_set_action_default(cls, group, action, *args):
        group.set_defaults(command_action=action, command_action_arguments=args)

    def _run(self):
        run = getattr(self, self._options.command_action.replace('-', '_'))
        run(*self._options.command_action_arguments)

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
    def completer_info_attrs(cls, *, completer_attr=None, **kwargs):
        options = SimpleNamespace(verbose=False, dry_run=False, command_action='argcomplete', **kwargs)
        parent = cls.parent_command_cls()(options=options, cache=Cache(), config=Config(), is_parent=True)
        return [getattr(info, completer_attr) if completer_attr else cls.azobject_class().info_id(info)
                for info in parent.azobject.get_azsubobject_infos(cls.azobject_name())]

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
    def parser_add_action_arguments(cls, group):
        super().parser_add_action_arguments(group)
        cls.parser_add_action_argument_show(group)

    @classmethod
    def parser_add_action_argument_show(cls, group):
        return cls._parser_add_action_argument(group, '--show',
                                               help=f'Show default {cls.command_text()} (default)')

    @classmethod
    def parser_set_action_default(cls, group):
        cls._parser_set_action_default(group, 'show')

    def show(self):
        self.azobject.show()


class CreateActionCommand(ActionCommand, AzObjectCommand):
    @classmethod
    def parser_add_action_arguments(cls, group):
        super().parser_add_action_arguments(group)
        cls.parser_add_action_argument_create(group)

    @classmethod
    def parser_add_action_argument_create(cls, group):
        return cls._parser_add_action_argument(group, '-c', '--create',
                                               help=f'Create a {cls.command_text()}')

    @property
    def azobject_default_id(self):
        if self._options.command_action == 'create' and not self.is_parent:
            raise RequiredArgument(self.azobject_name(), 'create')
        return super().azobject_default_id

    def create(self):
        self.azobject.create(**vars(self._options))


class DeleteActionCommand(ActionCommand, AzObjectCommand):
    @classmethod
    def parser_add_action_arguments(cls, group):
        super().parser_add_action_arguments(group)
        cls.parser_add_action_argument_delete(group)

    @classmethod
    def parser_add_action_argument_delete(cls, group):
        return cls._parser_add_action_argument(group, '-d', '--delete',
                                               help=f'Delete a {cls.command_text()}')

    def delete(self):
        self.azobject.delete(**vars(self._options))


class ListActionCommand(ActionCommand, AzSubCommand):
    @classmethod
    def parser_add_action_arguments(cls, group):
        super().parser_add_action_arguments(group)
        cls.parser_add_action_argument_list(group)

    @classmethod
    def parser_add_action_argument_list(cls, group):
        return cls._parser_add_action_argument(group, '-l', '--list',
                                               help=f'List {cls.command_text()}s')

    def list(self):
        self.azclass.list(self.parent_azobject, **vars(self._options))


class SetActionCommand(ActionCommand, AzSubCommand):
    @classmethod
    def parser_add_action_arguments(cls, group):
        super().parser_add_action_arguments(group)
        cls.parser_add_action_argument_set(group)

    @classmethod
    def parser_add_action_argument_set(cls, group):
        return cls._parser_add_action_argument(group, '-S', '--set',
                                               help=f'Set default {cls.command_text()}')

    def set(self):
        self.azobject.set_default(**vars(self._options))


class ClearActionCommand(ActionCommand, AzSubCommand):
    @classmethod
    def parser_add_action_arguments(cls, group):
        super().parser_add_action_arguments(group)
        cls.parser_add_action_argument_clear(group)

    @classmethod
    def parser_add_action_argument_clear(cls, group):
        return cls._parser_add_action_argument(group, '-C', '--clear',
                                               help=f'Clear default {cls.command_text()}')

    def clear(self):
        self.azobject.clear_default(**vars(self._options))


class AllActionCommand(CreateActionCommand, DeleteActionCommand, SetActionCommand, ClearActionCommand, ListActionCommand, ShowActionCommand):
    pass
