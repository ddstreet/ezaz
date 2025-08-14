
import subprocess

from contextlib import contextmanager
from contextlib import suppress

from ..argutil import ArgMap
from ..argutil import FlagArgConfig
from ..exception import AlreadyLoggedIn
from ..exception import AlreadyLoggedOut
from ..exception import AzCommandError
from ..exception import ConfigNotFound
from ..exception import DefaultConfigNotFound
from ..exception import NotLoggedIn
from .azobject import AzShowable
from .azobject import AzSubObjectContainer


class Account(AzShowable, AzSubObjectContainer):
    @classmethod
    def azobject_name_list(cls):
        return ['account']

    @classmethod
    def get_child_classes(cls):
        from .subscription import Subscription
        return [Subscription]

    @classmethod
    def get_self_id_argconfig(cls, is_parent):
        return []

    @classmethod
    def get_login_action_config(cls):
        return cls.make_action_config('login', cmd=['login'], description='Login')

    @classmethod
    def get_login_action_argconfigs(cls):
        return [FlagArgConfig('use_device_code', help='Instead of opening a browser window, show the URL and code')]

    @classmethod
    def get_logout_action_config(cls):
        return cls.make_action_config('logout', cmd=['logout'], description='Logout')

    @classmethod
    def get_action_configmap(cls):
        return ArgMap(super().get_action_configmap(), login=cls.get_login_action_config(), logout=cls.get_logout_action_config())

    @property
    def config(self):
        return self._config.get_object(self.info().user.name)

    def get_self_id(self, is_parent):
        return {}

    @property
    def azobject_id(self):
        return NotImplemented

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

    def login(self, **opts):
        if self.is_logged_in:
            raise AlreadyLoggedIn()

        with self._disable_subscription_selection():
            self.do_action(actioncfg=self.get_login_action_config(), **opts)

        self._logged_in = True
        with suppress(DefaultConfigNotFound):
            # Switch subscriptions, if needed
            self.set_current_subscription_id(self.get_default_child_id(Subscription.azobject_name()))

    def logout(self, **opts):
        if not self.is_logged_in:
            raise AlreadyLoggedOut()

        self.do_action(actioncfg=self.get_logout_action_config(), **opts)
        self._logged_in = False
        with suppress(AttributeError):
            del self._cached_info

    @property
    def is_logged_in(self):
        with suppress(AttributeError):
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
        return self.info().id

    def set_current_subscription_id(self, subscription):
        if self.get_current_subscription_id() != subscription:
            self.az('account', 'set', cmd_args={'-s': subscription}, dry_runnable=False)
        with suppress(AttributeError):
            del self._cached_info
