
from .command import AzCommonActionCommand


class MarketplaceOfferCommand(AzCommonActionCommand):
    @classmethod
    def azclass(cls):
        from ..azobject.marketplaceoffer import MarketplaceOffer
        return MarketplaceOffer
