
import getpass
import random
import string

from contextlib import suppress
from functools import cached_property

from ..argutil import ArgConfig
from ..argutil import ArgMap
from ..argutil import AzObjectArgConfig
from ..argutil import BoolArgConfig
from ..dialog import AzObjectChoice
from ..dialog import YesNo
from ..exception import ChoiceError
from ..exception import DefaultConfigNotFound
from ..exception import NoChoices
from ..exception import NoneOfTheAboveChoice
from .command import ActionCommand


class SetupCommand(ActionCommand):
    @classmethod
    def command_name_list(cls):
        return ['setup']

    @classmethod
    def get_action_configs(cls):
        return [*super().get_action_configs(),
                cls.get_prompt_action_config(),
                cls.get_create_action_config()]

    @classmethod
    def get_prompt_action_config(cls):
        return cls.make_action_config('prompt',
                                      description='Prompt to select the default object, if needed',
                                      argconfigs=cls.get_prompt_action_argconfigs())

    @classmethod
    def get_prompt_action_argconfigs(cls):
        return [BoolArgConfig('all', help=f'Prompt for all object types, even ones with a default'),
                BoolArgConfig('verify_single', help=f'Prompt even if there is only one object choice'),
                BoolArgConfig('y', 'yes', help=f'Respond yes to all yes/no questions')]

    @classmethod
    def get_create_action_config(cls):
        return cls.make_action_config('create',
                                      description='Automatically create a new default object, if needed',
                                      argconfigs=cls.get_create_action_argconfigs())

    @classmethod
    def get_create_action_argconfigs(cls):
        from ..azobject.location import Location
        from ..azobject.subscription import Subscription
        return [AzObjectArgConfig('subscription', azclass=Subscription, help='Subscription to use (instead of prompting to choose)'),
                AzObjectArgConfig('location', azclass=Location, help='Location to use (instead of prompting to choose)'),
                BoolArgConfig('all', help=f'Create all object types, even ones with a default'),
                BoolArgConfig('y', 'yes', help=f'Respond yes to all yes/no questions')]

    @classmethod
    def get_default_action(cls):
        return None

    @property
    def yes(self):
        return getattr(self.options, 'yes', False)

    @property
    def all(self):
        return getattr(self.options, 'all', False)

    @property
    def verify_single(self):
        return getattr(self.options, 'verify_single', False)

    @property
    def subscription(self):
        return getattr(self.options, 'subscription', False)

    @property
    def location(self):
        return getattr(self.options, 'location', False)

    def randomhex(self, n):
        return ''.join(random.choices(string.hexdigits.lower(), k=n))

    @property
    def _user(self):
        from ..azobject.user import User
        return User.get_instance(**self.opts)

    @property
    def user(self):
        if not self._user.is_logged_in:
            print("You are not logged in, so let's log you in first.")
            self._user.login()
        return self._user

    def get_default_child(self, container, name):
        objtype = container.get_child_class(name).azobject_text()
        print(f'Checking for default {objtype}: ', end='\n' if self.verbose else '', flush=True)

        with suppress(DefaultConfigNotFound):
            default = container.get_default_child(name)
            if default.exists:
                return default
            print(f'current default {default.azobject_text()} ({default.azobject_id}) does not exist...', end='\n' if self.verbose else '', flush=True)
        return None

    def choose_child(self, container, name, *, cmdline_arg_id=None, **kwargs):
        objtype = container.get_child_class(name).azobject_text()
        default = self.get_default_child(container, name)
        if self.all or default is None:
            if default is None:
                print('no default, checking available...')
            else:
                print(default.azobject_id)
            default = None
            if cmdline_arg_id:
                default = container.get_child(name, cmdline_arg_id)
                if not default.exists:
                    print('Provided {objtype} {cmdline_arg_id} does not exist, please choose another...')
                    default = None
            if not default:
                try:
                    default = AzObjectChoice(container.get_children(name), default, verify_single=self.verify_single, **kwargs)
                except NoChoices:
                    print(f'No {objtype} found, please create at least one; skipping')
                    raise
                except NoneOfTheAboveChoice:
                    print(f'No {objtype} selected; skipping')
                    raise
            container.set_default_child_id(name, default.azobject_id)
            print(f'Default {objtype} is {default.azobject_id}')
        else:
            print(default.azobject_id)

        return default

    def prompt(self, **opts):
        self.choose_subscription()
        print('All done.')

    def choose_subscription(self):
        with suppress(NoneOfTheAboveChoice):
            subscription = self.choose_child(self.user, 'subscription', cmdline_arg_id=self.subscription, hint_fn=lambda o: o.info().id)

            self.add_resource_group_filter(subscription)
            self.choose_location(subscription)
            self.choose_resource_group(subscription)

    def choose_location(self, subscription):
        return self.choose_child(subscription, 'location', cmdline_arg_id=self.location)

    def add_resource_group_filter(self, subscription):
        rgfilter = subscription.get_child_filter('resource_group')
        if not rgfilter:
            if self.yes or YesNo('Do you want to set up a resource group prefix filter (recommended for shared subscriptions)?'):
                username = getpass.getuser()
                accountname = self.user.info().userPrincipalName.split('@')[0]
                if self.yes or YesNo(f"Do you want to use prefix matching with your username '{username}'?"):
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
            rg = self.choose_child(subscription, 'resource_group')

            self.choose_storage_account(rg)
            self.choose_image_gallery(rg)
            self.choose_ssh_key(rg)
            self.choose_vm(rg)

    def choose_storage_account(self, rg):
        with suppress(ChoiceError):
            sa = self.choose_child(rg, 'storage_account')
            self.choose_storage_key(sa)
            self.choose_storage_container(sa)

    def choose_storage_key(self, sa):
        if sa.allow_shared_key_access:
            with suppress(ChoiceError):
                self.choose_child(sa, 'storage_key', cmdline_arg_id='key1')

    def choose_storage_container(self, sa):
        with suppress(ChoiceError):
            self.choose_child(sa, 'storage_container')

    def choose_image_gallery(self, rg):
        with suppress(ChoiceError):
            ig = self.choose_child(rg, 'image_gallery')
            self.choose_image_definition(ig)

    def choose_image_definition(self, ig):
        with suppress(ChoiceError):
            self.choose_child(ig, 'image_definition')

    def choose_ssh_key(self, rg):
        with suppress(ChoiceError):
            self.choose_child(rg, 'ssh_key')

    def choose_vm(self, rg):
        with suppress(ChoiceError):
            self.choose_child(rg, 'vm')

    def create_child(self, container, name, **kwargs):
        objtype = container.get_child_class(name).azobject_text()
        default = self.get_default_child(container, name)
        if self.all or default is None:
            if default is None:
                print('no default, creating one...')
            else:
                print(default.azobject_id)
            default_id = f'{self.prefix}{self.randomhex(8)}'
            default = container.get_child(name, default_id)
            kwargs[name] = default_id
            default.create(**kwargs)
            print(f'Created {objtype} {default.azobject_id}')
            default.parent.set_default_child_id(name, default.azobject_id)
            print(f'Default {objtype} is {default.azobject_id}')
        else:
            print(default.azobject_id)

        return default

    def create(self, **opts):
        self.create_subscription()
        print('All done.')

    def create_subscription(self):
        with suppress(NoneOfTheAboveChoice):
            subscription = self.choose_child(self.user, 'subscription', cmdline_arg_id=self.subscription, hint_fn=lambda o: o.info().id)
            self.add_resource_group_filter(subscription)
            location = self.choose_location(subscription)
            self.create_resource_group(subscription, location)

    def create_resource_group(self, subscription, location):
        rg = self.create_child(subscription, 'resource_group', location=location.azobject_id)

        self.create_storage_account(rg)
        self.create_image_gallery(rg)
        self.create_ssh_key(rg)

    def create_storage_account(self, rg):
        sa = self.create_child(rg, 'storage_account')
        self.choose_storage_key(sa)
        self.create_storage_container(sa)

    def create_storage_container(self, sa):
        self.create_child(sa, 'storage_container')

    def create_image_gallery(self, rg):
        ig = self.create_child(rg, 'image_gallery')
        self.create_image_definition(ig)

    def create_image_definition(self, ig):
        self.create_child(ig, 'image_definition',
                          offer=f'{self.prefix}offer{self.randomhex(8)}',
                          publisher=f'{self.prefix}publisher{self.randomhex(8)}',
                          sku=f'{self.prefix}sku{self.randomhex(8)}',
                          os_type='Linux')

    def create_ssh_key(self, rg):
        self.create_child(rg, 'ssh_key')
