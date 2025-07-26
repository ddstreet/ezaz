
from contextlib import suppress
from functools import cached_property

from ..azobject.account import Account
from ..config import Config
from ..exception import AlreadyLoggedIn
from ..exception import AlreadyLoggedOut
from ..exception import NotLoggedIn
from .command import ActionParser
from .command import ShowActionCommand


class AccountCommand(ShowActionCommand):
    @classmethod
    def azobject_class(cls):
        return Account

    @classmethod
    def parser_get_action_parsers(cls):
        return (super().parser_get_action_parsers() +
                [ActionParser('login', description='Login'),
                 ActionParser('logout', description='Logout'),
                 ActionParser('relogin', description='Logout (if needed), then login')])

    @classmethod
    def parser_add_login_action_arguments(cls, parser):
        parser.add_argument('--use-device-code',
                            action='store_true',
                            help='Instead of opening a browser window, show the URL and code')

    @classmethod
    def parser_add_relogin_action_arguments(cls, parser):
        cls.parser_add_login_action_arguments(parser)

    @classmethod
    def cls_login(cls, azobject, use_device_code=False):
        already = False
        try:
            azobject.login(use_device_code=use_device_code)
        except AlreadyLoggedIn:
            already = True
        cls.cls_show(azobject, already=already)

    @classmethod
    def cls_logout(cls, azobject):
        already = False
        try:
            azobject.logout()
        except AlreadyLoggedOut:
            already = True
        cls.cls_show(azobject, already=already)

    @classmethod
    def cls_show(cls, azobject, already=False):
        logged = 'Already logged' if already else 'Logged'
        try:
            info = azobject.info
            print(f"{logged} in as '{info.user.name}' using subscription '{info.name}' (id {info.id})")
        except NotLoggedIn:
            print(f"{logged} out")

    def login(self):
        self.cls_login(self.azobject, self._options.use_device_code)

    def logout(self):
        self.cls_logout(self.azobject)

    def relogin(self):
        with suppress(AlreadyLoggedOut):
            self.azobject.logout()
        self.login()

    def show(self):
        self.cls_show(self.azobject)
