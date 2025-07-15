
from contextlib import suppress

from ..azobject.account import Account
from ..exception import AlreadyLoggedIn
from ..exception import AlreadyLoggedOut
from ..exception import NotLoggedIn
from .command import Command


class AccountCommand(Command):
    @classmethod
    def name(cls):
        return 'account'

    @classmethod
    def _parser_add_arguments(cls, parser):
        parser.add_argument('--use-device-code',
                            action='store_true',
                            help='Instead of opening a browser window, show the URL and code')

        title_group = parser.add_argument_group('Action', 'Action to perform')
        group = title_group.add_mutually_exclusive_group()
        group.add_argument('--login',
                           action='store_true',
                           help='Login (if needed)')
        group.add_argument('--logout',
                           action='store_true',
                           help='Logout (if needed)')
        group.add_argument('--relogin',
                           action='store_true',
                           help='Logout (if needed), then login')
        group.add_argument('--show',
                           action='store_true',
                           help='Show login details (default)')

    def _run(self):
        if self._options.login:
            self.login()
        elif self._options.logout:
            self.logout()
        elif self._options.relogin:
            self.relogin()
        else: # default
            self.show()

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
