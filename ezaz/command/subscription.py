
from ..azobject.subscription import Subscription
from ..exception import DefaultConfigNotFound
from ..exception import RequiredArgument
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
    def completer_subscription_name(cls, **kwargs):
        parent = cls.parent_command_cls().completer_azobject(**kwargs)
        return [o.info.name for o in parent.get_azsubobjects(cls.azobject_name())]

    @classmethod
    def parser_add_argument_obj_id(cls, parser):
        group = parser.add_mutually_exclusive_group()
        group.add_argument('--subscription-name',
                           help=f'Use the specified subscription, instead of the default').completer = cls.completer_subscription_name
        group.add_argument(f'--subscription',
                           help=f'Use the specified subscription, instead of the default').completer = cls.completer_obj_id

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
        self.parent_azobject.get_azsubobject(self.azobject_name(), self.parent_azobject.get_current_subscription_id()).show()

    def set_current(self):
        if not self._options.subscription:
            try:
                if self.parent_azobject.get_current_subscription_id() == self.azobject_default_id:
                    # If current == default, user must provide id
                    raise RequiredArgument('subscription', 'set_current')
            except DefaultConfigNotFound:
                raise RequiredArgument('subscription', 'set_current')
        # User specified the sub id, or current != default (so we will set current to default)
        self.parent_azobject.set_current_subscription_id(self.azobject_id)

    def set(self):
        if self._options.subscription:
            print(f"Provided subscription '{self._options.subscription}' ignored, using current subscription.")
        self.parent_azobject.set_azsubobject_default_id(self.azobject_name(), self.parent_azobject.get_current_subscription_id())
