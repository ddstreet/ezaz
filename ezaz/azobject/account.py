
import subprocess

from contextlib import contextmanager
from contextlib import suppress

from ..exception import AlreadyLoggedIn
from ..exception import AlreadyLoggedOut
from ..exception import ConfigNotFound
from ..exception import NotLoggedIn
from ..exception import SubscriptionConfigNotFound
from . import AzObject
from .subscription import Subscription


class Account(AzObject):
    def __init__(self, config, info=None):
        self._top_config = config
        self._info = info

    @property
    def config(self):
        return self._top_config.get_account(self.info.user.name)

    @property
    def verbose(self):
        return self._top_config.verbose

    @property
    def dry_run(self):
        return self._top_config.dry_run

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
            self.default_subscription = self.config.default_subscription

    def logout(self):
        if not self.is_logged_in:
            raise AlreadyLoggedOut()

        self.az('logout')
        self._info = None

    @property
    def is_logged_in(self):
        try:
            self.info
            return True
        except NotLoggedIn:
            return False

    @property
    def info(self):
        if self.dry_run:
            raise NotLoggedIn()
        if not self._info:
            self._info = self.az_response('account', 'show')
        return self._info

    @property
    def default_subscription(self):
        with suppress(SubscriptionConfigNotFound):
            return self.config.default_subscription
        return self.info.id

    @default_subscription.setter
    def default_subscription(self, subscription):
        if self.default_subscription != subscription:
            self.az('account', 'set', '-s', subscription)
            self._info = None

    @default_subscription.deleter
    def default_subscription(self, subscription):
        del self.config.default_subscription

    def get_subscription(self, subscription, info=None):
        return Subscription(subscription, self, info=info)

    def get_default_subscription(self):
        return self.get_subscription(self.default_subscription)

    def get_subscriptions(self):
        return [self.get_subscription(info.id, info=info)
                for info in self.az_responselist('account', 'list')]
