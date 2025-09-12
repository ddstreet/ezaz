
import getpass
import random
import string

from contextlib import suppress
from functools import cache
from functools import cached_property

from ..argutil import ArgConfig
from ..argutil import ArgMap
from ..argutil import AzObjectArgConfig
from ..argutil import BoolArgConfig
from ..argutil import GroupArgConfig
from ..cache import CacheExpiry
from ..dialog import AzObjectChoice
from ..dialog import YesNo
from ..exception import ChoiceError
from ..exception import DefaultConfigNotFound
from ..exception import NoChoices
from ..exception import NoneOfTheAboveChoice
from .command import ActionCommand


class SetupCommand(ActionCommand):
    @classmethod
    @cache
    def cache_expiry_defaults(cls):
        from ..azobject.location import Location
        from ..azobject.marketplaceimage import MarketplaceImage
        from ..azobject.marketplaceoffer import MarketplaceOffer
        from ..azobject.marketplacepublisher import MarketplacePublisher
        from ..azobject.roleassignment import RoleAssignment
        from ..azobject.roledefinition import RoleDefinition
        from ..azobject.sshkey import SshKey
        from ..azobject.subscription import Subscription
        from ..azobject.vmdisktype import VmDiskType
        from ..azobject.vmhosttype import VmHostType
        from ..azobject.vminstancetype import VmInstanceType
        from ..azobject.vmsnapshottype import VmSnapshotType
        from ..azobject.user import User

        FOREVER = CacheExpiry.FOREVER

        return {
            'default': dict(show=3600, list=600),
            Location.azobject_name(): dict(show=FOREVER, list=FOREVER),
            MarketplaceImage.azobject_name(): dict(show=FOREVER, list=600),
            MarketplaceOffer.azobject_name(): dict(show=FOREVER, list=600),
            MarketplacePublisher.azobject_name(): dict(show=FOREVER, list=600),
            RoleAssignment.azobject_name(): dict(show=FOREVER, list=86400),
            RoleDefinition.azobject_name(): dict(show=FOREVER, list=86400),
            SshKey.azobject_name(): dict(show=FOREVER, list=600),
            Subscription.azobject_name(): dict(show=FOREVER, list=86400),
            VmDiskType.azobject_name(): dict(show=FOREVER, list=FOREVER),
            VmHostType.azobject_name(): dict(show=FOREVER, list=FOREVER),
            VmInstanceType.azobject_name(): dict(show=FOREVER, list=FOREVER),
            VmSnapshotType.azobject_name(): dict(show=FOREVER, list=FOREVER),
            User.azobject_name(): dict(show=FOREVER, list=600),
        }

    @classmethod
    def command_name_list(cls):
        return ['setup']

    @classmethod
    def get_action_configs(cls):
        return [*super().get_action_configs(),
                cls.get_prompt_action_config(),
                cls.get_create_action_config()]

    @classmethod
    def get_resources_argconfig_group(cls):
        from ..azobject.user import User
        return GroupArgConfig(*User.get_descendant_azobject_id_argconfigs(noncmd=True, help='Use {azobject_text}, instead of creating or prompting'),
                              title='Resource options')

    @classmethod
    def get_prompt_action_config(cls):
        return cls.make_action_config('prompt',
                                      description='Prompt to select the default object, if needed',
                                      argconfigs=cls.get_prompt_action_argconfigs())

    @classmethod
    def get_prompt_action_argconfigs(cls):
        return [cls.get_resources_argconfig_group(),
                GroupArgConfig(BoolArgConfig('all', help=f'Prompt for all object types, even ones with a default'),
                               BoolArgConfig('verify_single', help=f'Prompt even if there is only one object choice'),
                               BoolArgConfig('y', 'yes', help=f'Respond yes to all yes/no questions'),
                               title='Prompting options')]

    @classmethod
    def get_create_action_config(cls):
        return cls.make_action_config('create',
                                      description='Automatically create a new default object, if needed',
                                      argconfigs=cls.get_create_action_argconfigs())

    @classmethod
    def get_create_action_argconfigs(cls):
        return [cls.get_resources_argconfig_group(),
                GroupArgConfig(BoolArgConfig('all', help=f'Create all object types, even ones with a default'),
                               BoolArgConfig('y', 'yes', help=f'Respond yes to all yes/no questions'),
                               title='Creation options')]

    @classmethod
    def get_default_action(cls):
        return None

    def get_cache_expiry_builtin_default(self, key):
        return self.cache_expiry_defaults().get(key)

    def randomhex(self, n):
        return ''.join(random.choices(string.hexdigits.lower(), k=n))

    @property
    def user(self):
        from ..azobject.user import User
        return User.get_instance(**self.opts)

    def get_default_child(self, container, name):
        objtype = container.get_child_class(name).azobject_text()
        print(f'Checking for default {objtype}: ', end='\n' if self.verbose else '', flush=True)

        with suppress(DefaultConfigNotFound):
            default = container.get_default_child(name)
            if default.exists:
                return default
            print(f'current default {default.azobject_text()} ({default.azobject_id}) does not exist...', end='\n' if self.verbose else '', flush=True)
        return None

    def choose_child(self, container, name, *, hint_fn=None, verify_single=False, **opts):
        objtype = container.get_child_class(name).azobject_text()
        default = self.get_default_child(container, name)
        if opts.get('all') or default is None:
            if default is None:
                print('no default, checking available...')
            else:
                print(default.azobject_id)
            default = None
            if opts.get(name):
                default = container.get_child(name, opts.get(name))
                if not default.exists:
                    print(f'Provided {objtype} {opts.get(name)} does not exist, please choose another...')
                    default = None
            if not default:
                try:
                    default = AzObjectChoice(container.get_children(name), default, verify_single=verify_single, hint_fn=hint_fn)
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

    def create_child(self, container, name, **opts):
        objtype = container.get_child_class(name).azobject_text()
        default = self.get_default_child(container, name)
        if opts.get('all') or default is None:
            if default is None:
                print('no default, creating one...')
            else:
                print(default.azobject_id)
            default_id = f'{self.prefix}{self.randomhex(8)}'
            default = container.get_child(name, default_id)
            opts[name] = default_id
            default.create(**opts)
            print(f'Created {objtype} {default.azobject_id}')
            default.parent.set_default_child_id(name, default.azobject_id)
            print(f'Default {objtype} is {default.azobject_id}')
        else:
            print(default.azobject_id)

        return default

    def add_cache_config(self, yes=False, **opts):
        if not self.user.default_cache_expiry():
            if yes or YesNo('Do you want to set up cache expiration times using the default values?'):
                self.set_cache_config_defaults(**opts)
                print('Created cache expiration configuration with default values')
            else:
                print('Skipping the cache expiration time configuration')
        else:
            print('Existing default cache expiry; assuming all cache expiration times are already configured')

    def set_cache_config_defaults(self, **opts):
        self.set_cache_expiry_values(self.user.default_cache_expiry(), self.get_cache_expiry_builtin_default('default'))
        self.user.for_each_descendant_class(self.set_cache_expiry_values_from_azclass, None, include_self=True)

    def set_cache_expiry_values_from_azclass(self, azclass, opts):
        name = azclass.azobject_name()
        defaults = self.get_cache_expiry_builtin_default(name)
        if defaults:
            self.set_cache_expiry_values(self.user.cache_expiry(name), defaults)

    def set_cache_expiry_values(self, expiry, defaults):
        expiry.show_expiry = defaults['show']
        expiry.list_expiry = defaults['list']

    def add_resource_group_filter(self, sub, *, yes=False, **opts):
        rgfilter = sub.get_child_filter('resource_group')
        if not rgfilter:
            if yes or YesNo('Do you want to set up a resource group prefix filter (recommended for shared subscriptions)?'):
                username = getpass.getuser()
                accountname = self.user.info().userPrincipalName.split('@')[0]
                prefix = None
                if yes or YesNo(f"Do you want to use prefix matching with your username '{username}'?"):
                    prefix = username
                elif YesNo(f"Do you want to use prefix matching with your account name '{accountname}'?"):
                    prefix = accountname
                elif YesNo(f'Do you want to use a custom prefix?'):
                    prefix = input('What prefix do you want to use? ')
                if prefix:
                    rgfilter.prefix = prefix
                    print(f'Added resource group filter with prefix {rgfilter.prefix}')
                else:
                    print('Skipping the resource group prefix filter')
            else:
                print('Skipping the resource group prefix filter')
        else:
            if rgfilter.prefix:
                print(f"Existing resource group prefix filter: '{rgfilter.prefix}'")
        self.prefix = rgfilter.prefix or getpass.getuser()

    def prompt(self, **opts):
        self.add_cache_config(**opts)
        self.choose_subscription(**opts)
        print('All done.')

    def choose_subscription(self, **opts):
        with suppress(NoneOfTheAboveChoice):
            sub = self.choose_child(self.user, 'subscription', hint_fn=lambda o: o.info().id, **opts)
            self.add_resource_group_filter(sub, **opts)
            self.choose_location(sub, **opts)
            self.choose_resource_group(sub, **opts)

    def choose_location(self, sub, **opts):
        return self.choose_child(sub, 'location', **opts)

    def choose_resource_group(self, sub, **opts):
        with suppress(ChoiceError):
            rg = self.choose_child(sub, 'resource_group', **opts)
            self.choose_storage_account(rg, **opts)
            self.choose_image_gallery(rg, **opts)
            self.choose_ssh_key(rg, **opts)
            self.choose_vm(rg, **opts)

    def choose_storage_account(self, rg, **opts):
        with suppress(ChoiceError):
            sa = self.choose_child(rg, 'storage_account', **opts)
            self.choose_storage_key(sa, **opts)
            self.choose_storage_container(sa, **opts)

    def choose_storage_key(self, sa, **opts):
        if sa.allow_shared_key_access:
            with suppress(ChoiceError):
                self.choose_child(sa, 'storage_key', **opts)

    def choose_storage_container(self, sa, **opts):
        with suppress(ChoiceError):
            self.choose_child(sa, 'storage_container', **opts)

    def choose_image_gallery(self, rg, **opts):
        with suppress(ChoiceError):
            ig = self.choose_child(rg, 'image_gallery', **opts)
            self.choose_image_definition(ig, **opts)

    def choose_image_definition(self, ig, **opts):
        with suppress(ChoiceError):
            self.choose_child(ig, 'image_definition', **opts)

    def choose_ssh_key(self, rg, **opts):
        with suppress(ChoiceError):
            self.choose_child(rg, 'ssh_key', **opts)

    def choose_vm(self, rg, **opts):
        with suppress(ChoiceError):
            self.choose_child(rg, 'vm', **opts)

    def create(self, **opts):
        self.add_cache_config(**opts)
        self.create_subscription(**opts)
        print('All done.')

    def create_subscription(self, **opts):
        with suppress(NoneOfTheAboveChoice):
            sub = self.choose_child(self.user, 'subscription', hint_fn=lambda o: o.info().id, **opts)
            self.add_resource_group_filter(sub, **opts)
            location = self.choose_location(sub, **opts)
            self.create_resource_group(sub, **opts)

    def create_resource_group(self, sub, **opts):
        rg = self.create_child(sub, 'resource_group', **opts)
        self.create_storage_account(rg, **opts)
        self.create_image_gallery(rg, **opts)
        self.create_ssh_key(rg, **opts)

    def create_storage_account(self, rg, **opts):
        sa = self.create_child(rg, 'storage_account', **opts)
        self.choose_storage_key(sa, **opts)
        self.create_storage_container(sa, **opts)

    def create_storage_container(self, sa, **opts):
        self.create_child(sa, 'storage_container', **opts)

    def create_image_gallery(self, rg, **opts):
        ig = self.create_child(rg, 'image_gallery', **opts)
        self.create_image_definition(ig, **opts)

    def create_image_definition(self, ig, **opts):
        opts |= dict(offer=f'{self.prefix}offer{self.randomhex(8)}',
                     publisher=f'{self.prefix}publisher{self.randomhex(8)}',
                     sku=f'{self.prefix}sku{self.randomhex(8)}',
                     os_type='Linux')
        self.create_child(ig, 'image_definition', **opts)

    def create_ssh_key(self, rg, **opts):
        self.create_child(rg, 'ssh_key', **opts)
