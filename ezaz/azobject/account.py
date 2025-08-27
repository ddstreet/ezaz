
import subprocess

from contextlib import contextmanager
from contextlib import suppress
from functools import cached_property

from ..argutil import ArgMap
from ..argutil import FlagArgConfig
from ..cache import Cache
from ..config import Config
from ..exception import AlreadyLoggedIn
from ..exception import AlreadyLoggedOut
from ..exception import ArgumentError
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
        from .user import User
        return [Subscription, User]

    @classmethod
    def get_action_configs(cls):
        return [*super().get_action_configs(),
                cls.make_action_config('login', cmd=['login'], description='Login'),
                cls.make_action_config('logout', cmd=['logout'], description='Logout')]

    @classmethod
    def get_login_action_argconfigs(cls):
        return [FlagArgConfig('use_device_code', help='Instead of opening a browser window, show the URL and code')]

    @classmethod
    def get_self_id_argconfig(cls, **kwargs):
        return []

    def __init__(self, *, cachedir, configfile, **kwargs):
        super().__init__(cache=Cache(cachedir), config=Config(configfile), **kwargs)

    @cached_property
    def config(self):
        return super().config.get_object(self.info().user.name)

    def get_self_id_opts(self):
        return {}

    @property
    def azobject_id(self):
        return NotImplemented

    def show_pre(self, opts):
        return self.info_cache().get('account')

    def show_post(self, result, opts):
        self.info_cache()['account'] = result
        return result

    @contextmanager
    def login_context_manager(self):
        v = None
        try:
            with suppress(AzCommandError):
                v = self.az_info('config', 'get', cmd_args={'core.login_experience_v2': None}).value
            self.az_stdout('config', 'set', 'core.login_experience_v2=off')
            yield
        finally:
            if v is None:
                self.az_stdout('config', 'unset', 'core.login_experience_v2')
            elif v:
                self.az_stdout('config', 'set', f'core.login_experience_v2={v}')

    def login_pre(self, opts):
        if self.is_logged_in:
            raise AlreadyLoggedIn(self.info())

    def login(self, **opts):
        self.get_action_config('login').do_instance_action(self, opts)

    def login_post(self, result, opts):
        self._logged_in = True
        with suppress(DefaultConfigNotFound):
            # Switch subscriptions, if needed
            from .subscription import Subscription
            self.set_current_subscription_id(self.get_default_child_id(Subscription.azobject_name()))
        return result

    def logout_pre(self, opts):
        if not self.is_logged_in:
            raise AlreadyLoggedOut()

    def logout(self, **opts):
        self.get_action_config('logout').do_instance_action(self, opts)

    def logout_post(self, result, opts):
        self._logged_in = False
        self.info_cache().clear()
        return result

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
        self.info_cache().clear()

    def get_default_child_id(self, name):
        from .user import User
        if name == User.azobject_name():
            return User.get_null_instance().signed_in_user()._azobject_id
        return super().get_default_child_id(name)

    def set_default_child_id(self, name, value):
        from .user import User
        if name == User.azobject_name():
            raise ArgumentError('Cannot change default user id')
        return super().set_default_child_id(name, value)

    def del_default_child_id(self, name):
        from .user import User
        if name == User.azobject_name():
            raise ArgumentError('Cannot change default user id')
        return super().del_default_child_id(name)
