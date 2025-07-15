
from .account import AccountSubCommand
from .command import DefineSubCommand


class SubscriptionCommand(AccountSubCommand):
    @classmethod
    def command_name_list(cls):
        return ['subscription']

    @classmethod
    def aliases(cls):
        return ['sub']

    def _show(self, subscription):
        info = subscription.info
        print(f'{info.name} (id: {info.id})')


SubscriptionSubCommand = DefineSubCommand(AccountSubCommand, SubscriptionCommand)
