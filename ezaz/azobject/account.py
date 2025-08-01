
import subprocess

from contextlib import contextmanager
from contextlib import suppress

from ..argutil import ActionConfig
from ..argutil import ArgMap
from ..argutil import FlagArgConfig
from ..exception import AlreadyLoggedIn
from ..exception import AlreadyLoggedOut
from ..exception import AzCommandError
from ..exception import ConfigNotFound
from ..exception import NotLoggedIn
from .azobject import AzShowable
from .azobject import AzSubObjectContainer
from .subscription import Subscription


class Account(AzShowable, AzSubObjectContainer):
    @classmethod
    def azobject_name_list(cls):
        return ['account']

    @classmethod
    def get_azsubobject_classes(cls):
        return [Subscription]

    @classmethod
    def get_login_argconfig(cls):
        return [FlagArgConfig('use_device_code', help='Instead of opening a browser window, show the URL and code')]

    @classmethod
    def get_login_action_config(cls):
        return ActionConfig('login', description='Login', argconfigs=cls.get_login_argconfig())

    @classmethod
    def get_logout_action_config(cls):
        return ActionConfig('logout', description='Logout')

    @classmethod
    def get_action_configmap(cls):
        return ArgMap(super().get_action_configmap(), login=cls.get_login_action_config(), logout=cls.get_logout_action_config())

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._logged_in = None

    @property
    def config(self):
        return self._config.get_object(self.info.user.name)

    @property
    def azobject_id(self):
        return NotImplemented

    def get_cmd_args(self, cmdname, opts):
        return {}

    def get_subcmd_args(self, cmdname, opts):
        return {}

    @contextmanager
    def _disable_subscription_selection(self):
        v = None
        try:
            with suppress(AzCommandError):
                v = self.az_response('config', 'get', 'core.login_experience_v2').value
            self.az_stdout('config', 'set', 'core.login_experience_v2=off')
            yield
        finally:
            if v is None:
                self.az_stdout('config', 'unset', 'core.login_experience_v2')
            elif v:
                self.az_stdout('config', 'set', f'core.login_experience_v2={v}')

    def do_login_action(self, action, opts):
        if self.is_logged_in:
            raise AlreadyLoggedIn()

        with self._disable_subscription_selection():
            self.az('login', cmd_args=self.get_login_action_config().cmd_args(opts), dry_runnable=False)

        self._logged_in = True
        with suppress(KeyError):
            # Switch subscriptions, if needed
            self.set_current_subscription_id(self.config['default_subscription'])

    def do_logout_action(self, action, opts):
        if not self.is_logged_in:
            raise AlreadyLoggedOut()

        self.az('logout', dry_runnable=False)
        self._logged_in = False
        self._info = None

    @property
    def is_logged_in(self):
        if self._logged_in is not None:
            return self._logged_in
        try:
            # Unfortunately a simple 'account show' returns success
            # (sometimes) even when logged out; get-access-token seems
            # to be consistent about if we are actually logged in
            self.az_stdout('account', 'get-access-token')
            self._logged_in = True
        except NotLoggedIn:
            self._logged_in = False
        return self._logged_in

    def get_current_subscription_id(self):
        return self.info.id

    def set_current_subscription_id(self, subscription):
        if self.get_current_subscription_id() != subscription:
            self.az('account', 'set', cmd_args={'-s': subscription}, dry_runnable=False)
            self._info = None
