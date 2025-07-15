
from contextlib import suppress

from ..azobject.account import Account
from ..exception import AlreadyLoggedIn
from ..exception import AlreadyLoggedOut
from ..exception import NotLoggedIn
from .command import Command
from .command import DefineSubCommand
from .command import SubCommand


class AccountCommand(Command):
    @classmethod
    def command_name_list(cls):
        return ['account']

    @classmethod
    def parser_add_subclass_arguments(cls, parser):
        parser.add_argument('--use-device-code',
                            action='store_true',
                            help='Instead of opening a browser window, show the URL and code')

    @classmethod
    def parser_add_action_arguments(cls, group):
        cls._parser_add_action_argument(group, ['--login'], help=f'Login')
        cls._parser_add_action_argument(group, ['--logout'], help=f'Logout')
        cls._parser_add_action_argument(group, ['--relogin'], help=f'Logout (if needed), then login')
        cls._parser_add_action_argument(group, ['--show'], help=f'Show login details (default)')

    @classmethod
    def parser_add_argument_obj_id(cls, parser):
        pass

    def login(self):
        already = False
        try:
            self._account.login(use_device_code=self._options.use_device_code)
        except AlreadyLoggedIn:
            already = True
        self.show(already=already)

    def logout(self):
        already = False
        try:
            self._account.logout()
        except AlreadyLoggedOut:
            already = True
        self.show(already=already)

    def relogin(self):
        with suppress(AlreadyLoggedOut):
            self._account.logout()
        self.login()

    def show(self, already=False):
        logged = 'Already logged' if already else 'Logged'
        try:
            info = self._account.info
            print(f"{logged} in as '{info.user.name}' using subscription '{info.name}' (id {info.id})")
        except NotLoggedIn:
            print(f"{logged} out")

    @property
    def default_subscription(self):
        print('get default sub')
        return None

    @default_subscription.setter
    def default_subscription(self, subscription):
        print('set default sub to {subscription}')

    @default_subscription.deleter
    def default_subscription(self):
        print('del default sub')


class AccountSubCommand(DefineSubCommand(SubCommand, AccountCommand)):
    @property
    def azobject(self):
        return self._account

    @classmethod
    def parser_add_argument_all_obj_id(cls, parser):
        pass
