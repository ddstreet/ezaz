
import argparse
import getpass
import random
import string

from contextlib import suppress
from functools import cached_property

from ..azobject.account import Account
from ..dialog import AzObjectChoice
from ..dialog import YesNo
from ..exception import ChoiceError
from ..exception import DefaultConfigNotFound
from ..exception import NoChoices
from ..exception import NoneOfTheAboveChoice
from ..filter import FILTER_DEFAULT
from .command import ActionParserConfig
from .command import CreateActionCommand


class SetupCommand(CreateActionCommand):
    @classmethod
    def azobject_class(cls):
        return Account

    @classmethod
    def command_name_list(cls):
        return ['setup']

    @classmethod
    def parser_get_action_parsers(cls):
        return (super().parser_get_action_parsers() +
                [ActionParserConfig('prompt', description='Prompt to select the default for each object type (default)')])

    @classmethod
    def parser_add_prompt_action_arguments(cls, parser):
        parser.add_argument('--all', action='store_true',
                            help=f'Prompt for all object types, even ones with a default')
        parser.add_argument('--verify-single', action='store_true',
                            help=f'Prompt even if there is only one object choice')
        parser.add_argument('-y', '--yes', action='store_true',
                            help=f'Respond yes to all yes/no questions')

    @classmethod
    def parser_add_prompt_create_arguments(cls, parser):
        parser.add_argument('--all', action='store_true',
                            help=f'Create all object types, even ones with a default')
        parser.add_argument('--subscription',
                            help=f'Subscription to use (instead of prompting to choose)')
        parser.add_argument('--location',
                            help=f'Location to use (instead of prompting to choose)')
        parser.add_argument('-y', '--yes', action='store_true',
                            help=f'Respond yes to all yes/no questions')

    @classmethod
    def parser_get_create_action_description(cls):
        return 'Automatically create a new default object for all object types without a default'

    @classmethod
    def parser_get_action_default(cls):
        return 'prompt'

    @property
    def _yes(self):
        return getattr(self._options, 'yes', False)

    @property
    def _all(self):
        return getattr(self._options, 'all', False)

    @property
    def _verify_single(self):
        return getattr(self._options, 'verify_single', False)

    @property
    def _subscription(self):
        return getattr(self._options, 'subscription', False)

    @property
    def _location(self):
        return getattr(self._options, 'location', False)

    def randomhex(self, n):
        return ''.join(random.choices(string.hexdigits.lower(), k=n))

    @property
    def account(self):
        if not self.azobject.is_logged_in:
            print("You are not logged in, so let's log you in first.")
            self.azobject.login()
        return self.azobject

    def get_azsubobject_text(self, container, name):
        return container.get_azsubobject_class(name).azobject_text()

    def get_azsubobject_default(self, container, name):
        objtype = self.get_azsubobject_text(container, name)
        print(f'Checking for default {objtype}: ', end='\n' if self.verbose else '', flush=True)

        with suppress(DefaultConfigNotFound):
            default = container.get_azsubobject(name, container.get_azsubobject_default_id(name))
            if default.exists:
                return default
            print(f'current default {default.azobject_text()} ({default.azobject_id}) does not exist...', end='\n' if self.verbose else '', flush=True)
        return None

    def choose_azsubobject(self, container, name, *, cmdline_arg_id=None, **kwargs):
        objtype = self.get_azsubobject_text(container, name)
        default = self.get_azsubobject_default(container, name)
        if self._all or default is None:
            if default is None:
                print('no default, checking available...')
            else:
                print(default.azobject_id)
            default = None
            if cmdline_arg_id:
                default = container.get_azsubobject(name, cmdline_arg_id)
                if not default.exists:
                    print('Provided {objtype} {cmdline_arg_id} does not exist, please choose another...')
                    default = None
            if not default:
                try:
                    default = AzObjectChoice(container.get_azsubobjects(name), default, verify_single=self._verify_single, **kwargs)
                except NoChoices:
                    print(f'No {objtype} found, please create at least one; skipping')
                    raise
                except NoneOfTheAboveChoice:
                    print(f'No {objtype} selected; skipping')
                    raise
            container.set_azsubobject_default_id(name, default.azobject_id)
            print(f'Default {objtype} is {default.azobject_id}')
        else:
            print(default.azobject_id)

        return default

    def prompt(self):
        self.choose_subscription()
        print('All done.')

    def choose_subscription(self):
        with suppress(NoneOfTheAboveChoice):
            subscription = self.choose_azsubobject(self.account, 'subscription', arg_id=self._subscription, hint_fn=lambda o: o.info.name)

            self.add_resource_group_filter(subscription)
            self.choose_location(subscription)
            self.choose_resource_group(subscription)

    def choose_location(self, subscription):
        return self.choose_azsubobject(subscription, 'location')

    def add_resource_group_filter(self, subscription):
        rgfilter = subscription.filters.get_filter('resource_group')
        if subscription.filters.is_empty:
            if self._yes or YesNo('Do you want to set up a resource group prefix filter (recommended for shared subscriptions)?'):
                username = getpass.getuser()
                accountname = self.account.info.user.name.split('@')[0]
                if self._yes or YesNo(f"Do you want to use prefix matching with your username '{username}'?"):
                    rgfilter.prefix = username
                elif YesNo(f"Do you want to use prefix matching with your account name '{accountname}'?"):
                    rgfilter.prefix = accountname
                elif YesNo(f'Do you want to use a custom prefix?'):
                    prefix = input('What prefix do you want to use? ')
                    rgfilter.prefix = prefix
                else:
                    print('Skipping the resource group prefix filter')
        else:
            if rgfilter.prefix:
                print(f"Existing resource group prefix filter: '{rgfilter.prefix}'")
        self.prefix = rgfilter.prefix or getpass.getuser()

    def choose_resource_group(self, subscription):
        with suppress(ChoiceError):
            rg = self.choose_azsubobject(subscription, 'resource_group')

            self.choose_storage_account(rg)
            self.choose_image_gallery(rg)
            self.choose_ssh_key(rg)
            self.choose_vm(rg)

    def choose_storage_account(self, rg):
        with suppress(ChoiceError):
            sa = self.choose_azsubobject(rg, 'storage_account')
            self.choose_storage_container(sa)

    def choose_storage_container(self, sa):
        with suppress(ChoiceError):
            self.choose_azsubobject(sa, 'storage_container')

    def choose_image_gallery(self, rg):
        with suppress(ChoiceError):
            ig = self.choose_azsubobject(rg, 'image_gallery')
            self.choose_image_definition(ig)

    def choose_image_definition(self, ig):
        with suppress(ChoiceError):
            self.choose_azsubobject(ig, 'image_definition')

    def choose_ssh_key(self, rg):
        with suppress(ChoiceError):
            self.choose_azsubobject(rg, 'ssh_key')

    def choose_vm(self, rg):
        with suppress(ChoiceError):
            self.choose_azsubobject(rg, 'vm')

    def create_azsubobject(self, container, name, **kwargs):
        objtype = self.get_azsubobject_text(container, name)
        default = self.get_azsubobject_default(container, name)
        if self._all or default is None:
            if default is None:
                print('no default, creating one...')
            else:
                print(default.azobject_id)
            default_id = f'{self.prefix}{self.randomhex(8)}'
            default = container.get_azsubobject(name, default_id)
            if self.verbose:
                print(f'Creating {objtype} {default.azobject_id}')
            default.create(**kwargs)
            print(f'Created {objtype} {default.azobject_id}')
            default.set_self_default()
            print(f'Default {objtype} is {default.azobject_id}')
        else:
            print(default.azobject_id)

        return default

    def create(self):
        self.create_subscription()
        print('All done.')

    def create_subscription(self):
        with suppress(NoneOfTheAboveChoice):
            subscription = self.choose_azsubobject(self.account, 'subscription', arg_id=self._subscription, hint_fn=lambda o: o.info.name)
            self.add_resource_group_filter(subscription)
            location = self.choose_location(subscription)
            self.create_resource_group(subscription, location)

    def create_location(self, subscription):
        return self.choose_azsubobject(subscription, 'location', arg_id=self._location)

    def create_resource_group(self, subscription, location):
        rg = self.create_azsubobject(subscription, 'resource_group', location=location.azobject_id)

        self.create_storage_account(rg)
        self.create_image_gallery(rg)
        self.create_ssh_key(rg)

    def create_storage_account(self, rg):
        sa = self.create_azsubobject(rg, 'storage_account')
        self.create_storage_container(sa)

    def create_storage_container(self, sa):
        self.create_azsubobject(sa, 'storage_container')

    def create_image_gallery(self, rg):
        ig = self.create_azsubobject(rg, 'image_gallery')
        self.create_image_definition(ig)

    def create_image_definition(self, ig):
        self.create_azsubobject(ig, 'image_definition',
                                offer=f'{self.prefix}offer{self.randomhex(8)}',
                                publisher=f'{self.prefix}publisher{self.randomhex(8)}',
                                sku=f'{self.prefix}sku{self.randomhex(8)}',
                                os_type='Linux')

    def create_ssh_key(self, rg):
        self.create_azsubobject(rg, 'ssh_key')
