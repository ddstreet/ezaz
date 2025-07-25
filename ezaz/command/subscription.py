
from contextlib import suppress

from ..argutil import ArgMap
from ..exception import DefaultConfigNotFound
from ..exception import RequiredArgumentGroup
from .command import AzObjectActionCommand


class SubscriptionCommand(AzObjectActionCommand):
    @classmethod
    def azclass(cls):
        from ..azobject.subscription import Subscription
        return Subscription

    @classmethod
    def aliases(cls):
        return ['sub']
