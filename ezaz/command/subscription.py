
from ..azobject.subscription import Subscription
from .account import AccountCommand
from .command import ClearActionCommand
from .command import ListActionCommand
from .command import SetActionCommand
from .command import ShowActionCommand


class SubscriptionCommand(ClearActionCommand, ListActionCommand, SetActionCommand, ShowActionCommand):
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
    def parser_add_action_arguments(cls, group):
        super().parser_add_action_arguments(group)
        cls._parser_add_action_argument(group, '--show-current',
                                        help=f'Show current subscription')
        cls._parser_add_action_argument(group, '--set-current',
                                        help=f'Set current subscription (does not affect future logins)')

    @classmethod
    def parser_add_action_argument_set(cls, group):
        cls._parser_add_action_argument(group, '-S', '--set',
                                        help=f'Set default subscription to current subscription (future logins will automatically switch to this subscription)')

    @classmethod
    def parser_add_action_argument_clear(cls, group):
        cls._parser_add_action_argument(group, '-C', '--clear',
                                        help=f'Clear default subscription (future logins will use the az-provided default subscription)')

    def show_current(self):
        print(self.parent_azobject.get_current_subscription_id())

    def set_current(self):
        self.parent_azobject.set_current_subscription_id(self._options.subscription)

    def set(self):
        if self._options.subscription:
            print(f"Provided subscription '{self._options.subscription}' ignored, using current subscription.")
        self.parent_azobject.set_azsubobject_default_id(self.azobject_name(), self.parent_azobject.get_current_subscription_id())
