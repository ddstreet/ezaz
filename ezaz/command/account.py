
from contextlib import suppress

from ..argutil import ArgMap
from ..azobject.account import Account
from ..exception import AlreadyLoggedIn
from ..exception import AlreadyLoggedOut
from ..exception import NotLoggedIn
from .command import AzObjectActionCommand


class AccountCommand(AzObjectActionCommand):
    @classmethod
    def azclass(cls):
        return Account

    @classmethod
    def get_relogin_action_config(cls):
        return cls.make_action_config('relogin', description='Logout (if needed), then login', argconfigs=Account.get_login_argconfig())

    @classmethod
    def get_action_configmap(cls):
        configmap = super().get_action_configmap()
        configmap.get('show').cmdobjmethod = 'show'
        configmap.get('login').cmdobjmethod = 'login'
        configmap.get('logout').cmdobjmethod = 'logout'
        return ArgMap(configmap, relogin=cls.get_relogin_action_config())

    def show(self, already=False, **opts):
        logged = 'Already logged' if already else 'Logged'
        try:
            info = self.azobject.get_info(**opts)
            print(f"{logged} in as '{info.user.name}' using subscription '{info.name}' (id {info.id})")
        except NotLoggedIn:
            print(f"{logged} out")

    def login(self, show=True, **opts):
        already = False
        try:
            self.azobject.login(**opts)
        except AlreadyLoggedIn:
            already = True
        if show:
            self.show(already=already)

    def relogin(self, **opts):
        with suppress(AlreadyLoggedOut):
            self.logout(show=False)
        self.login()

    def logout(self, show=True, **opts):
        already = False
        try:
            self.azobject.logout(**opts)
        except AlreadyLoggedOut:
            already = True
        if show:
            self.show(already=already)
