
from .command import AccountSubCommand


class SubscriptionCommand(AccountSubCommand):
    @classmethod
    def _cls_type_list(cls):
        return ['subscription']

    @classmethod
    def aliases(cls):
        return ['sub']

    def _show(self, subscription):
        info = subscription.info
        print(f'{info.name} (id: {info.id})')
