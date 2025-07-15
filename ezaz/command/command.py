
import argparse
import json
import subprocess

from abc import ABC
from abc import abstractmethod

from ..azobject.account import Account
from ..exception import NotLoggedIn
from ..response import lookup_response


class Command(ABC):
    @classmethod
    @abstractmethod
    def name(cls):
        pass

    @classmethod
    def aliases(cls):
        return []

    @classmethod
    def parser_add_subparser(cls, subparsers):
        parser = subparsers.add_parser(cls.name(),
                                       aliases=cls.aliases())
        cls.parser_add_arguments(parser)
        parser.set_defaults(cls=cls)
        return parser

    @classmethod
    def parser_add_arguments(cls, parser):
        parser.add_argument('-v', '--verbose',
                            action='store_true',
                            help='Be verbose')
        parser.add_argument('-n', '--dry-run',
                            action='store_true',
                            help='Only print what would be done, do not run commands')
        cls._parser_add_arguments(parser)

    @classmethod
    def _parser_add_arguments(cls, parser):
        pass

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

    @abstractmethod
    def _run(self):
        pass

    def run(self):
        try:
            self._run()
        except NotLoggedIn:
            print('Not logged in, please log in and try again')


class AccountSubCommand(Command):
    @classmethod
    @abstractmethod
    def _cls_type_list(cls):
        # Return list of class type name strings, e.g. ['resource', 'group']
        pass

    @classmethod
    def _cls_type(cls, sep='_'):
        return sep.join(cls._cls_type_list())

    @classmethod
    def name(cls):
        return cls._cls_type(sep='')

    @classmethod
    def parser_add_arguments(cls, parser):
        super().parser_add_arguments(parser)

        class CommandAction(argparse.Action):
            def __call__(self, parser, namespace, values, option_string=None):
                namespace.command_action = self.option_strings[-1].lstrip('-')
                namespace.command_action_arguments = values

        clstype = cls._cls_type(sep=' ')
        metavar = cls._cls_type_list()[-1].upper()

        title_group = parser.add_argument_group('Action', 'Action to perform')
        group = title_group.add_mutually_exclusive_group()
        group.add_argument('-c', '--create', action=CommandAction, metavar=metavar,
                           help=f'Create a {clstype}')
        group.add_argument('--delete', action=CommandAction, metavar=metavar,
                           help=f'Delete a {clstype}')
        group.add_argument('-l', '--list', action=CommandAction, nargs=0,
                           help=f'List {clstype}s')
        group.add_argument('-C', '--clear', action=CommandAction, nargs=0,
                           help=f'Clear the default {clstype}')
        group.add_argument('-S', '--set', action=CommandAction, metavar=metavar,
                           help=f'Set the default {clstype}')
        group.add_argument('--show', action=CommandAction, nargs=0,
                           help=f'Show default {clstype} (default)')
        group.set_defaults(command_action='show', command_action_arguments=[])

    def _run(self):
        run = getattr(self, self._options.command_action)
        if self._options.command_action_arguments:
            run(self._options.command_action_arguments)
        else:
            run()

    @property
    def _parent(self):
        return self._account

    def create(self, target):
        print('IMPLEMENT ME!')

    def delete(self, target):
        print('IMPLEMENT ME!')

    def list(self):
        for target in getattr(self._parent, f'get_{self._cls_type()}s')():
            self._show(target)

    def clear(self):
        delattr(self._parent, f'default_{self._cls_type()}')

    def set(self, target):
        setattr(self._parent, f'default_{self._cls_type()}', target)

    def show(self):
        self._show(getattr(self._parent, f'get_default_{self._cls_type()}')())

    @abstractmethod
    def _show(self, target):
        pass


def DefineSubCommand(superclass, parent_cls_type_list):
    class SubCommand(superclass):
        @classmethod
        def parser_add_arguments(cls, parser):
            super().parser_add_arguments(parser)
            parser.add_argument(f"--{'-'.join(parent_cls_type_list)}",
                                help=f"Use the specified {' '.join(parent_cls_type_list)}, instead of the default")

        @property
        def _parent(self):
            arg = '_'.join(parent_cls_type_list)
            if getattr(self._options, arg):
                return getattr(super()._parent, f'get_{arg}')(getattr(self._options, arg))
            else:
                return getattr(super()._parent, f'get_default_{arg}')()

    return SubCommand


SubscriptionSubCommand = DefineSubCommand(AccountSubCommand, ['subscription'])
ResourceGroupSubCommand = DefineSubCommand(SubscriptionSubCommand, ['resource', 'group'])
ImageGallerySubCommand = DefineSubCommand(ResourceGroupSubCommand, ['image', 'gallery'])
StorageAccountSubCommand = DefineSubCommand(ResourceGroupSubCommand, ['storage', 'account'])
