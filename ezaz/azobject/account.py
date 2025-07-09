4
import json
import subprocess

from contextlib import contextmanager

from ..exception import AlreadyLoggedIn
from ..exception import AlreadyLoggedOut
from ..exception import ConfigNotFound
from ..exception import NotLoggedIn
from . import AzObject


class Account(AzObject):
    @classmethod
    def name(cls):
        return "account"

    def _setup(self):
        self._accountinfo = None

    @property
    def config(self):
        return self._config.get_account(self.accountinfo.user.name)

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

        try:
            # Switch subscriptions, if needed
            self.subscription = self.config.current_subscription
        except ConfigNotFound:
            # No saved subscription, save current one
            self.config.current_subscription = self.subscription

    def logout(self):
        if not self.is_logged_in:
            raise AlreadyLoggedOut()

        self.az('logout')
        self._accountinfo = None

    @property
    def is_logged_in(self):
        try:
            self.accountinfo
            return True
        except NotLoggedIn:
            return False

    @property
    def accountinfo(self):
        if not self._accountinfo:
            try:
                self._accountinfo = self.az_response('account', 'show')
            except subprocess.CalledProcessError:
                raise NotLoggedIn()
        return self._accountinfo

    @property
    def subscription(self):
        return self.accountinfo.id

    @subscription.setter
    def subscription(self, subscription):
        if self.subscription != subscription:
            self.az('set', '-s', subscription)
            self._accountinfo = None
            self.config.current_subscription = self.subscription

    @property
    def subscriptions(self):
        if not self.is_logged_in:
            raise NotLoggedIn()

        return self.az_responselist('account', 'list')
