
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
        self._setup()

    def _setup(self):
        pass

    @property
    def verbose(self):
        return self._config.verbose

    @property
    def dry_run(self):
        return self._config.dry_run

    @abstractmethod
    def _run(self):
        pass

    def run(self):
        try:
            self._run()
        except NotLoggedIn:
            print('Not logged in, please log in and try again')


class StandardActionCommand(Command):
    @classmethod
    def parser_add_arguments(cls, parser):
        super().parser_add_arguments(parser)

        class CommandAction(argparse.Action):
            def __call__(self, parser, namespace, values, option_string=None):
                namespace.command_action = self.option_strings[-1].lstrip('-')
                namespace.command_action_arguments = list(values)

        assert cls.ACTION_ARGUMENT_NAME, f'Class {cls.__name__} does not implement ACTION_ARGUMENT_NAME'
        assert cls.ACTION_ARGUMENT_METAVAR, f'Class {cls.__name__} does not implement ACTION_ARGUMENT_METAVAR'
        name = cls.ACTION_ARGUMENT_NAME
        metavar = cls.ACTION_ARGUMENT_METAVAR
        title_group = parser.add_argument_group('Action', 'Action to perform')
        group = title_group.add_mutually_exclusive_group()
        group.add_argument('--create', action=CommandAction, metavar=metavar,
                           help=f'Create a {name}')
        group.add_argument('--delete', action=CommandAction, metavar=metavar,
                           help=f'Delete a {name}')
        group.add_argument('--list', action=CommandAction, nargs=0,
                           help=f'List {name}s')
        group.add_argument('--clear', action=CommandAction, nargs=0,
                           help=f'Clear the current {name}')
        group.add_argument('--set', action=CommandAction, metavar=metavar,
                           help=f'Set the current {name}')
        group.add_argument('--show', action=CommandAction, nargs=0,
                           help=f'Show current {name} (default)')
        group.set_defaults(command_action='show', command_action_arguments=[])

    def _setup(self):
        super()._setup()
        assert self.ACTION_ATTR_PARENT, f'Class {self.__class__.__name__} does not implement ACTION_ATTR_PARENT'
        assert self.ACTION_ATTR_NAME, f'Class {self.__class__.__name__} does not implement ACTION_ATTR_NAME'

    def _run(self):
        run = getattr(self, self._options.command_action)
        run(*self._options.command_action_arguments)

    @property
    def _parent(self):
        return getattr(self, self.ACTION_ATTR_PARENT)

    def create(self, target):
        print('IMPLEMENT ME!')

    def delete(self, target):
        print('IMPLEMENT ME!')

    def list(self):
        for target in getattr(self._parent, f'get_{self.ACTION_ATTR_NAME}s')():
            self._show(target)

    def clear(self):
        delattr(self._parent, f'current_{self.ACTION_ATTR_NAME}')

    def set(self, target):
        setattr(self._parent, f'current_{self.ACTION_ATTR_NAME}', target)

    def show(self):
        self._show(getattr(self._parent, f'get_current_{self.ACTION_ATTR_NAME}')())

    @abstractmethod
    def _show(self, target):
        pass


class SubscriptionSubCommand(Command):
    ACTION_ATTR_PARENT = '_subscription'

    @classmethod
    def parser_add_arguments(cls, parser):
        super().parser_add_arguments(parser)

        parser.add_argument('--subscription',
                            help='Use the specified subscription, instead of the current subscription')

    def _setup(self):
        super()._setup()
        self._account = Account(self._config)

    @property
    def _subscription(self):
        if self._options.subscription:
            return self._account.get_subscription(self._options.subscription)
        else:
            return self._account.get_current_subscription()


class ResourceGroupSubCommand(SubscriptionSubCommand):
    ACTION_ATTR_PARENT = '_resource_group'

    @classmethod
    def parser_add_arguments(cls, parser):
        super().parser_add_arguments(parser)

        parser.add_argument('--resource-group',
                            help='Use the specified resource group, instead of the current resource group')

    @property
    def _resource_group(self):
        if self._options.resource_group:
            return self._subscription.get_resource_group(self._options.resource_group)
        else:
            return self._subscription.get_current_resource_group()


class ImageGallerySubCommand(ResourceGroupSubCommand):
    ACTION_ATTR_PARENT = '_image_gallery'

    @classmethod
    def parser_add_arguments(cls, parser):
        super().parser_add_arguments(parser)

        parser.add_argument('--image-gallery',
                            help='Use the specified image gallery, instead of the current image gallery')

    @property
    def _image_gallery(self):
        if self._options.image_gallery:
            return self._resource_group.get_image_gallery(self._options.image_gallery)
        else:
            return self._resource_group.get_current_image_gallery()


class StorageAccountSubCommand(ResourceGroupSubCommand):
    ACTION_ATTR_PARENT = '_storage_account'

    @classmethod
    def parser_add_arguments(cls, parser):
        super().parser_add_arguments(parser)

        parser.add_argument('--storage-account',
                            help='Use the specified storage account, instead of the current storage account')

    @property
    def _storage_account(self):
        if self._options.storage_account:
            return self._resource_group.get_storage_account(self._options.storage_account)
        else:
            return self._resource_group.get_current_storage_account()
