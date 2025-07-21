
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
    def command_name_list(cls):
        return ['subscription']

    @classmethod
    def aliases(cls):
        return ['sub']

    @classmethod
    def parser_add_action_arguments(cls, group):
        super().parser_add_action_arguments(group)
        cls._parser_add_action_argument(group, '--set-current', nargs=1,
                                        help=f'Set current subscription (does not affect future logins)')

    @classmethod
    def parser_add_action_argument_set(cls, group):
        cls._parser_add_action_argument(group, '-S', '--set',
                                        help=f'Set default subscription to current subscription (future logins will automatically switch to this subscription)')

    @classmethod
    def parser_add_action_argument_clear(cls, group):
        cls._parser_add_action_argument(group, '-C', '--clear',
                                        help=f'Clear default subscription (future logins will use the az-provided default subscription)')

    @property
    def _default_azobject_id(self):
        return self.parent_azobject.get_current_subscription_id()

    def set_current(self, subscription):
        self.parent_azobject.set_current_subscription_id(subscription)
