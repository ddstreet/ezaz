
from contextlib import contextmanager

from ..exception import AlreadyLoggedIn
from ..exception import AlreadyLoggedOut
from ..exception import ConfigNotFound
from ..exception import NotLoggedIn
from . import AzObject
from .subscription import Subscription


class Account(AzObject):
    def __init__(self, config, info=None):
        self._config = config
        self._account_info = info

    @property
    def config(self):
        return self._config.get_account(self.account_info.user.name)

    @contextmanager
    def _disable_subscription_selection(self):
        v = None
        unset = False
        try:
            try:
                r = self.az_response('config', 'get', 'core.login_experience_v2')
                if r:
                    v = r.value
            except subprocess.CalledProcessError:
                unset = True
            self.az_stdout('config', 'set', 'core.login_experience_v2=off')
            yield
        finally:
            if unset:
                self.az_stdout('config', 'unset', 'core.login_experience_v2')
            elif v:
                self.az_stdout('config', 'set', f'core.login_experience_v2={v}')

    def login(self, use_device_code=False):
        if self.is_logged_in:
            raise AlreadyLoggedIn()

        cmd = ['login']
        if use_device_code:
            cmd.append('--use-device-code')
        with self._disable_subscription_selection():
            self.az(*cmd)

        with suppress(ConfigNotFound):
            # Switch subscriptions, if needed
            self.current_subscription = self.config.current_subscription

    def logout(self):
        if not self.is_logged_in:
            raise AlreadyLoggedOut()

        self.az('logout')
        self._account_info = None

    @property
    def is_logged_in(self):
        try:
            self.account_info
            return True
        except NotLoggedIn:
            return False

    @property
    def account_info(self):
        if not self._account_info:
            self._account_info = self.az_response('account', 'show')
        return self._account_info

    @property
    def current_subscription(self):
        return self.account_info.id

    @current_subscription.setter
    def current_subscription(self, subscription):
        if self.current_subscription != subscription:
            self.az('account', 'set', '-s', subscription)
            self._account_info = None

    def get_subscription(self, subscription, info=None):
        return Subscription(subscription, self, info=info)

    def get_current_subscription(self):
        return self.get_subscription(self.current_subscription)

    def get_subscriptions(self):
        return [self.get_subscription(info.id, info=info)
                for info in self.az_responselist('account', 'list')]
