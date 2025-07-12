
from contextlib import suppress

from ..azobject.account import Account
from ..exception import AccountConfigNotFound
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

        title_group = parser.add_argument_group('Action', 'Action to perform (default is --show)')
        group = title_group.add_mutually_exclusive_group()
        group.add_argument('-i', '--login',
                           action='store_true',
                           help='Login (if needed)')
        group.add_argument('-o', '--logout',
                           action='store_true',
                           help='Logout (if needed)')
        group.add_argument('-r', '--relogin',
                           action='store_true',
                           help='Logout (if needed), then login')
        group.add_argument('--list',
                           action='store_true',
                           help='List available subscriptions')
        group.add_argument('--clear',
                           action='store_true',
                           help='Clear the current subscription; future logins will not switch the subscription')
        group.add_argument('--set',
                           help='Set the current subscription; future logins will switch to this subscription if needed')
        group.add_argument('--show',
                           action='store_true',
                           help='Show login details')

    def _setup(self):
        self._account = Account(config=self._config)

    def _run(self):
        if self._options.login:
            self.login()
        elif self._options.logout:
            self.logout()
        elif self._options.relogin:
            self.relogin()
        elif self._options.list:
            self.list()
        elif self._options.clear:
            self.clear()
        elif self._options.set:
            self.set(self._options.set)
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

    def clear(self):
        with suppress(AccountConfigNotFound):
            del self._account.config.current_subscription

    def set(self, subscription):
        self._account.subscription = subscription

    def list(self):
        for s in self._account.subscriptions:
            print(f'{s.name} (id: {s.id})')

    def show(self, already=False):
        logged = 'Already logged' if already else 'Logged'
        try:
            info = self._account.accountinfo
            print(f"{logged} in as '{info.user.name}' using subscription '{info.name}' (id {info.id})")
        except NotLoggedIn:
            print(f"{logged} out")
