
from contextlib import suppress

from ..azobject.subscription import Subscription
from ..exception import DefaultConfigNotFound
from ..exception import RequiredArgumentGroup
from .account import AccountCommand
from .command import ArgConfig
from .command import RoActionCommand


class SubscriptionCommand(RoActionCommand):
    @classmethod
    def parent_command_cls(cls):
        return AccountCommand

    @classmethod
    def azobject_class(cls):
        return Subscription

    @classmethod
    def aliases(cls):
        return ['sub']

    @classmethod
    def parser_get_action_names(cls):
        return super().parser_get_action_names() + ['show-current', 'set-current']

    @classmethod
    def parser_get_show_current_action_config(cls):
        return ArgConfig('show-current', description='Show current subscription')

    @classmethod
    def parser_get_set_current_action_config(cls):
        return ArgConfig('set-current', description='Set current subscription (does not affect future logins)')

    @classmethod
    def parser_get_set_action_description(cls):
        return f'Set default subscription to current subscription (future logins will automatically switch to this subscription)'

    @classmethod
    def parser_get_clear_action_description(cls):
        return f'Clear default subscription (future logins will use the az-provided default subscription)'

    @classmethod
    def _parser_add_argument_azobject_id(cls, parser, parent):
        group = parser.add_mutually_exclusive_group()
        group.add_argument('--subscription-name',
                           help=f'Use the specified subscription, instead of the default').completer = cls.completer_names
        group.add_argument(f'--subscription',
                           help=f'Use the specified subscription, instead of the default').completer = cls.completer_azobject_ids

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

    def do_show_current(self):
        self.parent_azobject.get_azsubobject(self.azobject_name(), self.parent_azobject.get_current_subscription_id()).show()

    def do_set_current(self):
        if not self.azobject_specified_id:
            try:
                if self.parent_azobject.get_current_subscription_id() == self.azobject_default_id:
                    # If current == default, user must provide id
                    raise RequiredArgumentGroup(['subscription', 'subscription_name'], '--set-current')
            except DefaultConfigNotFound:
                raise RequiredArgumentGroup(['subscription', 'subscription_name'], '--set-current')
        # User specified the sub id, or current != default (so we will set current to default)
        self.parent_azobject.set_current_subscription_id(self.azobject_id)

    def do_set(self):
        if self.azobject_specified_id:
            print(f"Provided subscription '{self.azobject_specified_id}' ignored, using current subscription.")
        self.parent_azobject.set_azsubobject_default_id(self.azobject_name(), self.parent_azobject.get_current_subscription_id())
