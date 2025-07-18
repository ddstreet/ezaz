
import argparse
import json
import subprocess

from abc import ABC
from abc import abstractmethod
from contextlib import suppress
from operator import methodcaller

from ..exception import NotLoggedIn
from ..response import lookup_response


class SimpleCommand(ABC):
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
        parser.add_argument('-v', '--verbose', action='store_true',
                            help='Be verbose')

    @classmethod
    def parser_add_argument_dry_run(cls, parser):
        parser.add_argument('-n', '--dry-run', action='store_true',
                            help='Only print what would be done, do not run commands')

    def __init__(self, config, options):
        self._config = config
        self._options = options
        self._setup()

    def _setup(self):
        pass

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
        group.add_argument(*args, action=CommandArgumentAction, nargs=nargs, metavar=cls.command_metavar(), help=help)

    @classmethod
    @abstractmethod
    def parser_set_action_default(cls, group):
        pass

    @classmethod
    def _parser_set_action_default(cls, group, action, *args):
        group.set_defaults(command_action=action, command_action_arguments=args)

    def _run(self):
        run = getattr(self, self._options.command_action)
        run(*self._options.command_action_arguments)

    def run(self):
        try:
            self._run()
        except NotLoggedIn as nli:
            print(str(nli))


class AzObjectCommand(SimpleCommand):
    @classmethod
    def parser_add_common_arguments(cls, parser):
        super().parser_add_common_arguments(parser)
        cls.parser_add_argument_obj_id(parser)

    @classmethod
    def parser_add_argument_obj_id(cls, parser):
        parser.add_argument(f'--{cls.command_name("-")}',
                            help=f'Use the specified {cls.command_text()}, instead of the default')

    @property
    @abstractmethod
    def azobject(self):
        pass


class SubAzObjectCommand(AzObjectCommand):
    @classmethod
    @abstractmethod
    def parent_command_cls(cls):
        pass

    @classmethod
    def parser_add_argument_obj_id(cls, parser):
        cls.parent_command_cls().parser_add_argument_obj_id(parser)
        super().parser_add_argument_obj_id(parser)

    def _setup(self):
        super()._setup()
        _parent_command = self.parent_command_cls()(self._config, self._options)
        assert isinstance(_parent_command, AzObjectCommand)
        self._parent_azobject = _parent_command.azobject

    @property
    def parent_azobject(self):
        return self._parent_azobject

    @property
    def _default_azobject_id_key(self):
        return f'default_{self.command_name()}'

    @property
    def _default_azobject_id(self):
        return getattr(self.parent_azobject, self._default_azobject_id_key)

    @property
    def _azobject_id(self):
        return getattr(self._options, self.command_name()) or self._default_azobject_id

    @property
    def azobject(self):
        return getattr(self.parent_azobject, f'get_{self.command_name()}')(self._azobject_id)


class ShowActionCommand(ActionCommand, AzObjectCommand):
    @classmethod
    def parser_add_action_arguments(cls, group):
        super().parser_add_action_arguments(group)
        cls.parser_add_action_argument_show(group)

    @classmethod
    def parser_add_action_argument_show(cls, group):
        cls._parser_add_action_argument(group, '--show',
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
        cls._parser_add_action_argument(group, '-c', '--create',
                                        help=f'Create a {cls.command_text()}')

    def create(self):
        self.azobject.create(**vars(self._options))


class DeleteActionCommand(ActionCommand, AzObjectCommand):
    @classmethod
    def parser_add_action_arguments(cls, group):
        super().parser_add_action_arguments(group)
        cls.parser_add_action_argument_delete(group)

    @classmethod
    def parser_add_action_argument_delete(cls, group):
        cls._parser_add_action_argument(group, '-d', '--delete',
                                        help=f'Delete a {cls.command_text()}')

    def delete(self):
        self.azobject.delete(**vars(self._options))


class ListActionCommand(ActionCommand, SubAzObjectCommand):
    @classmethod
    def parser_add_action_arguments(cls, group):
        super().parser_add_action_arguments(group)
        cls.parser_add_action_argument_list(group)

    @classmethod
    def parser_add_action_argument_list(cls, group):
        cls._parser_add_action_argument(group, '-l', '--list',
                                        help=f'List {cls.command_text()}s')

    def list(self):
        for azobject in getattr(self.parent_azobject, f'get_{self.command_name()}s')(**vars(self._options)):
            azobject.show()


class SetActionCommand(ActionCommand, SubAzObjectCommand):
    @classmethod
    def parser_add_action_arguments(cls, group):
        super().parser_add_action_arguments(group)
        cls.parser_add_action_argument_set(group)

    @classmethod
    def parser_add_action_argument_set(cls, group):
        cls._parser_add_action_argument(group, '-S', '--set',
                                        help=f'Set default {cls.command_text()}')

    def set(self):
        setattr(self.parent_azobject, self._default_azobject_id_key, self.azobject_id)


class ClearActionCommand(ActionCommand, SubAzObjectCommand):
    @classmethod
    def parser_add_action_arguments(cls, group):
        super().parser_add_action_arguments(group)
        cls.parser_add_action_argument_clear(group)

    @classmethod
    def parser_add_action_argument_clear(cls, group):
        cls._parser_add_action_argument(group, '-C', '--clear',
                                        help=f'Clear default {cls.command_text()}')

    def clear(self):
        delattr(self.parent_azobject, self._default_azobject_id_key)


class AllActionCommand(CreateActionCommand, DeleteActionCommand, SetActionCommand, ClearActionCommand, ListActionCommand, ShowActionCommand):
    pass
