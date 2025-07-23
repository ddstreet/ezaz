
import argparse

from contextlib import suppress
from functools import cached_property

from ..azobject.account import Account
from ..dialog import AzObjectChoice
from ..dialog import YesNo
from ..exception import DefaultConfigNotFound
from .account import AccountCommand
from .command import ActionCommand


class SetupCommand(ActionCommand):
    @classmethod
    def command_name_list(cls):
        return ['setup']

    @classmethod
    def parser_add_action_arguments(cls, group):
        super().parser_add_action_arguments(group)
        cls._parser_add_action_argument(group, '--prompt',
                                        help=f'Prompt for only missing default object types (default)')
        cls._parser_add_action_argument(group, '--prompt-all',
                                        help=f'Prompt for all object types, even ones with a default')
        cls._parser_add_action_argument(group, '-C', '--create',
                                        help=f'Automatically create any missing default object types')

    @classmethod
    def parser_set_action_default(cls, group):
        cls._parser_set_action_default(group, 'prompt')

    @cached_property
    def account(self):
        account = Account(self._config, verbose=self.verbose, dry_run=self.dry_run)
        if not account.is_logged_in:
            print("You are not logged in, so let's log you in first.")
            account.login()
        return account

    def check_azsubobject(self, container, name, cls, all=False):
        default = None
        with suppress(DefaultConfigNotFound):
            default = container.get_azsubobject(name, container.get_azsubobject_default_id(name))
            if not default.exists:
                print(f'Current default {name} ({default.azobject_id}) does not exist.')
                default = None

        if all or default is None:
            choices = container.get_azsubobjects(name)
            if not choices:
                print(f'No {name} found, please create at least one; skipping for now')
                return
            default = AzObjectChoice(cls, choices, default)
            container.set_azsubobject_default_id(name, default.azobject_id)

        print(f'Default {name} is {default.azobject_id}')

        if default.is_azsubobject_container():
            self.check_azsubobject_container(default, all=all)

    def check_azsubobject_container(self, container, all=False):
        assert container.is_azsubobject_container()
        for name, cls in container.get_azsubobject_classmap().items():
            self.check_azsubobject(container, name, cls, all=all)

    def prompt(self):
        self.check_azsubobject_container(self.account)

    def prompt_all(self):
        self.check_azsubobject_container(self.account, all=True)

    def create(self):
        raise NotImplementedError()
