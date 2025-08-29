
from contextlib import contextmanager
from contextlib import suppress
from functools import cached_property

from ..argutil import FlagArgConfig
from ..cache import Cache
from ..config import Config
from ..exception import AlreadyLoggedIn
from ..exception import AlreadyLoggedOut
from ..exception import AzCommandError
from ..exception import DefaultConfigNotFound
from ..exception import NotLoggedIn
from .azobject import AzListable
from .azobject import AzShowable
from .azobject import AzObjectContainer


class User(AzShowable, AzListable, AzObjectContainer):
    @classmethod
    def azobject_name_list(cls):
        return ['user']

    @classmethod
    def get_cmd_base(cls):
        return ['ad', 'user']

    @classmethod
    def get_child_classes(cls):
        from .subscription import Subscription
        return [Subscription]

    @classmethod
    def get_signed_in_user_instance(cls, user=None, **opts):
        return cls.get_instance(**opts)

    @classmethod
    def _get_specified_instance(cls, azobject_id, opts):
        return cls(azobject_id=azobject_id, **opts)

    @classmethod
    def get_default_azobject_id(cls, **opts):
        return cls.get_null_instance(**opts).signed_in_user(**opts)._id

    @classmethod
    def get_self_id_argconfigs(cls, is_parent=False, **kwargs):
        if is_parent:
            return []
        return super().get_self_id_argconfigs(is_parent=is_parent, **kwargs)

    @classmethod
    def get_self_id_argconfig_cmddest(cls, is_parent):
        return 'id'

    @classmethod
    def get_action_configs(cls):
        return [*super().get_action_configs(),
                cls.make_action_config('signed_in_user',
                                       get_instance=cls.get_null_instance,
                                       cmd=['ad', 'signed-in-user', 'show'],
                                       common_argconfigs=[],
                                       az='info',
                                       description='Show signed-in user'),
                cls.make_action_config('login',
                                       get_instance=cls.get_null_instance,
                                       cmd=['login'],
                                       common_argconfigs=[],
                                       description='Login',
                                       argconfigs=[FlagArgConfig('use_device_code',
                                                                 help='Instead of opening a browser window, show the URL and code')]),
                cls.make_action_config('logout',
                                       get_instance=cls.get_null_instance,
                                       cmd=['logout'],
                                       common_argconfigs=[],
                                       description='Logout')]

    def signed_in_user_pre(self, opts):
        return getattr(self.__class__, '_signed_in_user_info', None)

    def signed_in_user(self, **opts):
        return self.get_action_config('signed_in_user').do_instance_action(self, opts)

    def signed_in_user_post(self, result, opts):
        self.__class__._signed_in_user_info = result
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
            raise AlreadyLoggedIn(self.signed_in_user(**opts))

    def login(self, **opts):
        self.get_action_config('login').do_instance_action(self, opts)

    def login_post(self, result, opts):
        with suppress(DefaultConfigNotFound):
            # Switch subscriptions, if needed
            from .subscription import Subscription
            default_subscription = self.get_signed_in_user_instance(**opts).get_default_child(Subscription.azobject_name())
            default_subscription.set_current(subscription=default_subscription.azobject_id)
        return result

    def logout_pre(self, opts):
        if not self.is_logged_in:
            raise AlreadyLoggedOut()

    def logout(self, **opts):
        self.get_action_config('logout').do_instance_action(self, opts)

    def logout_post(self, result, opts):
        # TODO - technically, we should clear all subclass info caches
        # too, and maybe instance caches
        self.__class__._signed_in_user_info = None
        self.info_cache().clear()
        return result

    @property
    def is_logged_in(self):
        with suppress(NotLoggedIn):
            return self.signed_in_user() is not None
        return False
