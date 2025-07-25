
from .command import AzObjectActionCommand


class MarketplacePublisherCommand(AzObjectActionCommand):
    @classmethod
    def azclass(cls):
        from ..azobject.marketplacepublisher import MarketplacePublisher
        return MarketplacePublisher
