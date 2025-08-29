
from .command import AzObjectActionCommand


class MarketplaceOfferCommand(AzObjectActionCommand):
    @classmethod
    def azclass(cls):
        from ..azobject.marketplaceoffer import MarketplaceOffer
        return MarketplaceOffer
