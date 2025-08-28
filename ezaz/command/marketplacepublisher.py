
from .command import AzCommonActionCommand


class MarketplacePublisherCommand(AzCommonActionCommand):
    @classmethod
    def azclass(cls):
        from ..azobject.marketplacepublisher import MarketplacePublisher
        return MarketplacePublisher
