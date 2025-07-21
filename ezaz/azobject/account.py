
import subprocess

from contextlib import contextmanager
from contextlib import suppress

from ..exception import AlreadyLoggedIn
from ..exception import AlreadyLoggedOut
from ..exception import ConfigNotFound
from ..exception import NotCreatable
from ..exception import NotDeletable
from ..exception import NotLoggedIn
from .azobject import AzSubObjectContainer
from .subscription import Subscription


class Account(AzSubObjectContainer):
    @classmethod
    def get_base_cmd(cls):
        return ['account']

    @classmethod
    def get_create_cmd(cls):
        raise NotCreatable('account')

    @classmethod
    def get_delete_cmd(cls):
        raise NotDeletable('account')

    @classmethod
    def get_azsubobject_classes(cls):
        return [Subscription]

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

        cmd_args = {'--use-device-code': None} if use_device_code else {}
        with self._disable_subscription_selection():
            self.az('login', cmd_args=cmd_args)

        with suppress(KeyError):
            # Switch subscriptions, if needed
            self.set_current_subscription_id(self.config['default_subscription'])

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

    def get_current_subscription_id(self):
        return self.info.id

    def set_current_subscription_id(self, subscription):
        if self.get_current_subscription_id() != subscription:
            self.az('account', 'set', cmd_args={'-s': subscription}, dry_runnable=False)
            self._info = None
