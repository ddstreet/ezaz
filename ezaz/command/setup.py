
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

    @classmethod
    def parser_add_prompt_create_arguments(cls, parser):
        parser.add_argument('--all', action='store_true',
                            help=f'Create all object types, even ones with a default')

    @classmethod
    def parser_get_create_action_description(cls):
        return 'Automatically create a new default object for all object types without a default'

    @classmethod
    def parser_get_action_default(cls):
        return 'prompt'

    @property
    def _all(self):
        return getattr(self._options, 'all', False)

    @property
    def _verify_single(self):
        return getattr(self._options, 'verify_single', False)

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

    def get_azsubobject_default(self, container, name, does_not_exist_action):
        objtype = self.get_azsubobject_text(container, name)
        print(f'Checking for default {objtype}: ', end='\n' if self.verbose else '', flush=True)

        with suppress(DefaultConfigNotFound):
            default = container.get_azsubobject(name, container.get_azsubobject_default_id(name))
            if default.exists:
                return default
            print(f'Current default {default.azobject_text()} ({default.azobject_id}) does not exist, {does_not_exist_action}.')
        return None

    def choose_azsubobject(self, container, name, **kwargs):
        objtype = self.get_azsubobject_text(container, name)
        default = self.get_azsubobject_default(container, name, 'please choose another')
        if self._all or default is None:
            if default is None:
                print('no default, checking available...')
            else:
                print(default.azobject_id)
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

    def create(self):
        self.choose_subscription(create=True)

    def choose_subscription(self, create=False):
        with suppress(NoneOfTheAboveChoice):
            subscription = self.choose_azsubobject(self.account, 'subscription', hint_fn=lambda o: o.info.name)
            self.add_resource_group_filter(subscription)
            location = self.choose_location(subscription)

            if create:
                self.create_resource_group(subscription, location)
            else:
                self.choose_resource_group(subscription)

    def choose_location(self, subscription):
        return self.choose_azsubobject(subscription, 'location')

    def add_resource_group_filter(self, subscription):
        rgfilter = subscription.filters.get_filter('resource_group')
        if subscription.filters.is_empty:
            if YesNo('Do you want to set up a resource group prefix filter (recommended for shared subscriptions)?'):
                username = getpass.getuser()
                accountname = self.account.info.user.name.split('@')[0]
                if YesNo(f"Do you want to use prefix matching with your username '{username}'?"):
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
        default = self.get_azsubobject_default(container, name, 'creating new one')
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

    def create_resource_group(self, subscription, location):
        rg = self.create_azsubobject(subscription, 'resource_group', location=location.azobject_id)

        self.create_storage_account(rg)
        self.create_image_gallery(rg)
        self.create_ssh_key(rg)
        self.create_vm(rg)

    def create_storage_account(self, rg):
        sa = self.create_azsubobject(rg, 'storage_account')
        self.create_storage_container(sa)

    def create_storage_container(self, sa):
        self.create_azsubobject(sa, 'storage_container')

    def create_image_gallery(self, rg):
        ig = self.create_azsubobject(rg, 'image_gallery')
        self.create_image_definition(ig)

    def create_image_definition(self, ig):
        self.create_azsubobject(ig, 'image_definition')

    def create_ssh_key(self, rg):
        self.create_azsubobject(rg, 'ssh_key')

    def create_vm(self, rg):
        self.create_azsubobject(rg, 'vm')
