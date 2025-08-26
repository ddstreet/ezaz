
from contextlib import suppress

from ..argutil import ArgMap
from ..exception import DefaultConfigNotFound
from ..exception import RequiredArgumentGroup
from .command import AzSubObjectActionCommand


class SubscriptionCommand(AzSubObjectActionCommand):
    @classmethod
    def parent_command_cls(cls):
        from .account import AccountCommand
        return AccountCommand

    @classmethod
    def azclass(cls):
        from ..azobject.subscription import Subscription
        return Subscription

    @classmethod
    def aliases(cls):
        return ['sub']

    @classmethod
    def parser_get_show_current_action_config(cls):
        return cls.make_action_config('show-current', description='Show current subscription')

    @classmethod
    def parser_get_set_current_action_config(cls):
        return cls.make_action_config('set-current', description='Set current subscription (does not affect future logins)')

    @classmethod
    def parser_get_set_action_builtin_description(cls):
        return f'Set default subscription to current subscription (future logins will automatically switch to this subscription)'

    @classmethod
    def parser_get_clear_action_builtin_description(cls):
        return f'Clear default subscription (future logins will use the az-provided default subscription)'

    @classmethod
    def get_action_configs(cls):
        return [*super().get_action_configs(),
                cls.parser_get_show_current_action_config(),
                cls.parser_get_set_current_action_config()]

    @classmethod
    def _subscription_name_to_id(self, name):
        for s in self.parent_azobject.get_azsubobject_infos(self.azobject_name()):
            if s.name == name:
                return s.id
        raise NoAzObjectExists(name, None)

    @property
    def azobject_specified_id(self):
        with suppress(AttributeError):
            if self._options.subscription:
                return self._options.subscription
        with suppress(AttributeError):
            if self._options.subscription_name:
                return self._subscription_name_to_id(self._options.subscription_name)
        return None

    def show_current(self):
        self.parent_azobject.get_azsubobject(self.azobject_name(), self.parent_azobject.get_current_subscription_id()).show()

    def set_current(self):
        if not self.azobject_specified_id:
            try:
                if self.parent_azobject.get_current_subscription_id() == self.azobject_default_id:
                    # If current == default, user must provide id
                    raise RequiredArgumentGroup(['subscription', 'subscription_name'], '--set-current')
            except DefaultConfigNotFound:
                raise RequiredArgumentGroup(['subscription', 'subscription_name'], '--set-current')
        # User specified the sub id, or current != default (so we will set current to default)
        self.parent_azobject.set_current_subscription_id(self.azobject_id)

    def set(self):
        if self.azobject_specified_id:
            print(f"Provided subscription '{self.azobject_specified_id}' ignored, using current subscription.")
        self.parent_azobject.set_azsubobject_default_id(self.azobject_name(), self.parent_azobject.get_current_subscription_id())
