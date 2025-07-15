
import subprocess

from contextlib import contextmanager
from contextlib import suppress

from ..exception import AlreadyLoggedIn
from ..exception import AlreadyLoggedOut
from ..exception import ConfigNotFound
from ..exception import NotLoggedIn
from . import AzSubObjectContainer
from .subscription import Subscription


class Account(AzSubObjectContainer([Subscription])):
    def __init__(self, config, verbose=False, dry_run=False):
        super().__init__(config)
        self._verbose = verbose
        self._dry_run = dry_run

    @property
    def config(self):
        return self._config.get_object(self.info.user.name)

    @property
    def verbose(self):
        return self._verbose

    @property
    def dry_run(self):
        return self._dry_run

    def show_cmd(self):
        return ['account', 'show']

    def cmd_opts(self):
        return []

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

        with suppress(KeyError):
            # Switch subscriptions, if needed
            self.default_subscription = self.config['default_subscription']

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
    def current_subscription(self):
        return self.info.id

    @current_subscription.setter
    def current_subscription(self, subscription):
        if self.current_subscription != subscription:
            self.az('account', 'set', '-s', subscription)
            self._info = None
