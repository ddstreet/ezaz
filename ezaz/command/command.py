
import argparse
import json
import subprocess

from abc import ABC
from abc import abstractmethod
from contextlib import suppress

from ..azobject.account import Account
from ..exception import NotLoggedIn
from ..response import lookup_response


class Command(ABC):
    @classmethod
    @abstractmethod
    def command_name_list(cls):
        pass

    @classmethod
    def command_name(cls, sep='_'):
        return sep.join(cls.command_name_list())

    @classmethod
    def command_metavar(cls):
        return cls.command_name_list()[-1].upper()

    @classmethod
    def aliases(cls):
        return []

    @classmethod
    def parser_add_subparser(cls, subparsers):
        parser = subparsers.add_parser(cls.command_name(sep=''), aliases=cls.aliases())
        cls.parser_add_arguments(parser)
        parser.set_defaults(command_class=cls)
        return parser

    @classmethod
    def parser_add_arguments(cls, parser):
        cls.parser_add_argument_verbose(parser)
        cls.parser_add_argument_dry_run(parser)
        cls.parser_add_argument_obj_id(parser)

        cls.parser_add_subclass_arguments(parser)

        group = cls.parser_add_action_group(parser)
        cls.parser_add_action_arguments(group)
        cls.parser_set_action_default(group)

    @classmethod
    def parser_add_argument_verbose(cls, parser):
        parser.add_argument('-v', '--verbose', action='store_true',
                            help='Be verbose')

    @classmethod
    def parser_add_argument_dry_run(cls, parser):
        parser.add_argument('-n', '--dry-run', action='store_true',
                            help='Only print what would be done, do not run commands')

    @classmethod
    def parser_add_argument_obj_id(cls, parser):
        cls._parser_add_argument_obj_id(parser)

    @classmethod
    def _parser_add_argument_obj_id(cls, parser):
        parser.add_argument(f'--{cls.command_name("-")}',
                            help=f'Use the specified {cls.command_name(" ")}, instead of the default')

    @classmethod
    def parser_add_subclass_arguments(cls, parser):
        pass

    @classmethod
    def parser_add_action_group(cls, parser):
        title_group = parser.add_argument_group('Action', 'Action to perform')
        return title_group.add_mutually_exclusive_group()

    @classmethod
    @abstractmethod
    def parser_add_action_arguments(cls, group):
        pass

    @classmethod
    def _parser_add_action_argument(cls, group, opts, nargs=0, help=None):
        group.add_argument(*opts, action=CommandArgumentAction, nargs=nargs, metavar=cls.command_metavar(), help=help)

    @classmethod
    @abstractmethod
    def parser_set_action_default(cls, group):
        pass

    @classmethod
    def _parser_set_action_default(cls, group, action, *args):
        group.set_defaults(command_action=action, command_action_arguments=args)

    def __init__(self, config, options):
        self._config = config
        self._options = options
        self._account = Account(self._config, verbose=self.verbose, dry_run=self.dry_run)
        self._setup()

    def _setup(self):
        pass

    @property
    def verbose(self):
        return self._options.verbose

    @property
    def dry_run(self):
        return self._options.dry_run

    def _run(self):
        run = getattr(self, self._options.command_action)
        run(*self._options.command_action_arguments)

    def run(self):
        try:
            self._run()
        except NotLoggedIn as nli:
            print(str(nli))


class CommandArgumentAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        namespace.command_action = self.option_strings[-1].lstrip('-')
        namespace.command_action_arguments = values


class SubCommand(Command):
    @classmethod
    def parser_add_action_arguments(cls, group):
        cls.parser_add_action_argument_set(group)
        cls.parser_add_action_argument_clear(group)
        cls.parser_add_action_argument_create(group)
        cls.parser_add_action_argument_delete(group)
        cls.parser_add_action_argument_list(group)
        cls.parser_add_action_argument_show(group)

    @classmethod
    def parser_add_action_argument_set(cls, group):
        cls._parser_add_action_argument(group, ['-S', '--set'], nargs=1,
                                        help=f'Set default {cls.command_name(sep=" ")}')

    @classmethod
    def parser_add_action_argument_clear(cls, group):
        cls._parser_add_action_argument(group, ['-C', '--clear'],
                                        help=f'Clear default {cls.command_name(sep=" ")}')

    @classmethod
    def parser_add_action_argument_create(cls, group):
        cls._parser_add_action_argument(group, ['-c', '--create'], nargs=1,
                                        help=f'Create a {cls.command_name(sep=" ")}')

    @classmethod
    def parser_add_action_argument_delete(cls, group):
        cls._parser_add_action_argument(group, ['-d', '--delete'], nargs=1,
                                        help=f'Delete a {cls.command_name(sep=" ")}')

    @classmethod
    def parser_add_action_argument_list(cls, group):
        cls._parser_add_action_argument(group, ['-l', '--list'],
                                        help=f'List {cls.command_name(sep=" ")}s')

    @classmethod
    def parser_add_action_argument_show(cls, group):
        cls._parser_add_action_argument(group, ['--show'],
                                        help=f'Show default {cls.command_name(sep=" ")} (default)')

    @classmethod
    def parser_set_action_default(cls, group):
        cls._parser_set_action_default(group, 'show')

    @property
    def azobject(self):
        obj_id = getattr(self._options, self.command_name())
        if obj_id:
            return getattr(super().azobject, f'get_{self.command_name()}')(obj_id)
        else:
            return getattr(super().azobject, f'get_default_{self.command_name()}')()

    def create(self, target):
        print('IMPLEMENT ME!')

    def delete(self, target):
        print('IMPLEMENT ME!')

    @abstractmethod
    def _show(self, target):
        pass

    def show(self):
        self._show(self.azobject)

    def list(self):
        for target in getattr(self.azobject.parent, f'get_{self.command_name()}s')():
            self._show(target)

    def clear(self):
        delattr(self.azobject.parent, f'default_{self.command_name()}')

    def set(self, target):
        setattr(self.azobject.parent, f'default_{self.command_name()}', target)


def DefineSubCommand(superclass, parentclass):
    class InnerSubCommand(superclass):
        @classmethod
        def parent_command_cls(cls):
            return parentclass

        @classmethod
        def parser_add_argument_all_obj_id(cls, parser):
            cls.parent_command_cls().parser_add_argument_all_obj_id(parser)
            cls._parser_add_argument_obj_id(parser)

        @classmethod
        def parser_add_argument_obj_id(cls, parser):
            cls.parser_add_argument_all_obj_id(parser)
            
    return InnerSubCommand
