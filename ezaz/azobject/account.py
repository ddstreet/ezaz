
import subprocess

from contextlib import contextmanager
from contextlib import suppress

from ..exception import AlreadyLoggedIn
from ..exception import AlreadyLoggedOut
from ..exception import AzCommandError
from ..exception import ConfigNotFound
from ..exception import NotCreatable
from ..exception import NotDeletable
from ..exception import NotLoggedIn
from .azobject import AzSubObjectContainer
from .subscription import Subscription


class Account(AzSubObjectContainer):
    @classmethod
    def azobject_name_list(cls):
        return ['account']

    @classmethod
    def get_cmd(cls, cmdname):
        if cmdname == 'create':
            raise NotCreatable('account')
        if cmdname == 'delete':
            raise NotDeletable('account')
        return super().get_cmd(cmdname)

    @classmethod
    def get_azsubobject_classes(cls):
        return [Subscription]

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
            # Unfortunately a simple 'account show' returns success
            # (sometimes) even when logged out; get-access-token seems
            # to be consistent about if we are actually logged in
            self.az('account', 'get-access-token')
            return True
        except NotLoggedIn:
            return False

    def get_current_subscription_id(self):
        return self.info.id

    def set_current_subscription_id(self, subscription):
        if self.get_current_subscription_id() != subscription:
            self.az('account', 'set', cmd_args={'-s': subscription}, dry_runnable=False)
            self._info = None
