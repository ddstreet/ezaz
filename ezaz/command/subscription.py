
from contextlib import suppress

from ..argutil import ArgMap
from ..exception import DefaultConfigNotFound
from ..exception import RequiredArgumentGroup
from .command import AzCommonActionCommand


class SubscriptionCommand(AzCommonActionCommand):
    @classmethod
    def azclass(cls):
        from ..azobject.subscription import Subscription
        return Subscription

    @classmethod
    def aliases(cls):
        return ['sub']
