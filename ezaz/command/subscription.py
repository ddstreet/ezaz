
from .account import AccountCommand
from .command import SubCommand


class SubscriptionCommand(SubCommand):
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
    def parser_add_action_subclass_arguments(cls, group):
        cls._parser_add_action_argument(group, ['--set-current'], nargs=1,
                                        help=f'Set current subscription (does not affect future logins)')

    @classmethod
    def parser_add_action_argument_set(cls, group):
        cls._parser_add_action_argument(group, ['-S', '--set'], nargs=1,
                                        help=f'Set default subscription (current and future logins will switch to this subscription)')

    @classmethod
    def parser_add_action_argument_clear(cls, group):
        cls._parser_add_action_argument(group, ['-C', '--clear'],
                                        help=f'Clear default subscription (future logins will use the az-provided default subscription)')

    @property
    def _default_azobject_id_key(self):
        return f'current_{self.command_name()}'

    def set_current(self, subscription):
        self.parent_azobject.current_subscription = subscription

    def _show(self, subscription):
        info = subscription.info
        print(f'{info.name} (id: {info.id})')

