
import argparse

from contextlib import suppress
from functools import cached_property

from ..azobject.account import Account
from ..dialog import AzObjectChoice
from ..dialog import YesNo
from ..exception import ChoiceError
from ..exception import DefaultConfigNotFound
from ..exception import NoChoices
from ..exception import NoneOfTheAboveChoice
from .account import AccountCommand
from .command import ActionCommand


class SetupCommand(ActionCommand):
    @classmethod
    def command_name_list(cls):
        return ['setup']

    @classmethod
    def parser_add_common_arguments(cls, parser):
        super().parser_add_common_arguments(parser)
        parser.add_argument('--all', action='store_true',
                            help=f'Prompt for all object types, even ones with a default')
        parser.add_argument('--verify-single', action='store_true',
                            help=f'Prompt even if there is only one object choice')

    @classmethod
    def parser_add_action_arguments(cls, group):
        super().parser_add_action_arguments(group)
        cls._parser_add_action_argument(group, '--prompt',
                                        help=f'Prompt for only missing default object types (default)')
        cls._parser_add_action_argument(group, '--create',
                                        help=f'Automatically create any missing default object types')

    @classmethod
    def parser_set_action_default(cls, group):
        cls._parser_set_action_default(group, 'prompt')

    @property
    def all(self):
        return self._options.all

    @property
    def verify_single(self):
        return self._options.verify_single

    @cached_property
    def account(self):
        account = Account(self._config, verbose=self.verbose, dry_run=self.dry_run)
        if not account.is_logged_in:
            print("You are not logged in, so let's log you in first.")
            account.login()
        return account

    def get_azsubobject_default(self, container, name):
        with suppress(DefaultConfigNotFound):
            default = container.get_azsubobject(name, container.get_azsubobject_default_id(name))
            if default.exists:
                return default
            print(f'Current default {default.azobject_text()} ({default.azobject_id}) does not exist, please choose another.')
        return None

    def choose_azsubobject(self, container, name, **kwargs):
        objtype = container.get_azsubobject_class(name).azobject_text()
        print(f'Checking for default {objtype}: ', end='\n' if self.verbose else '', flush=True)

        default = self.get_azsubobject_default(container, name)
        if self.all or default is None:
            if default is None:
                print('no default, checking available...')
            else:
                print(default.azobject_id)
            try:
                default = AzObjectChoice(container.get_azsubobjects(name), default, verify_single=self.verify_single, **kwargs)
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
        raise NotImplementedError()

    def choose_subscription(self):
        with suppress(NoneOfTheAboveChoice):
            subscription = self.choose_azsubobject(self.account, 'subscription', hint_fn=lambda o: o.info.name)
            self.choose_resource_group(subscription)

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
