
from contextlib import suppress

from ..argutil import ActionConfig
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
        return ActionConfig('relogin', cmdobjmethod='relogin', description='Logout (if needed), then login', argconfigs=Account.get_login_argconfig())

    @classmethod
    def get_action_configmap(cls):
        configmap = super().get_action_configmap()
        configmap.get('show').cmdobjmethod = 'show'
        configmap.get('login').cmdobjmethod = 'login'
        configmap.get('logout').cmdobjmethod = 'logout'
        return ArgMap(configmap, relogin=cls.get_relogin_action_config())

    def show(self, action='show', opts={}, already=False):
        logged = 'Already logged' if already else 'Logged'
        try:
            info = self.azobject.get_info('show', opts=vars(self.options))
            print(f"{logged} in as '{info.user.name}' using subscription '{info.name}' (id {info.id})")
        except NotLoggedIn:
            print(f"{logged} out")

    def login(self, action='login', opts={}, show=True):
        already = False
        try:
            self.azobject.do_action(action=action, opts=opts)
        except AlreadyLoggedIn:
            already = True
        if show:
            self.show(already=already)

    def relogin(self, action='relogin', opts={}):
        with suppress(AlreadyLoggedOut):
            self.logout(show=False)
        self.login()

    def logout(self, action='logout', opts={}, show=True):
        already = False
        try:
            self.azobject.do_action(action=action, opts=opts)
        except AlreadyLoggedOut:
            already = True
        if show:
            self.show(already=already)
