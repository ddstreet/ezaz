
from .command import AzCommonActionCommand


class MarketplaceImageCommand(AzCommonActionCommand):
    @classmethod
    def azclass(cls):
        from ..azobject.marketplaceimage import MarketplaceImage
        return MarketplaceImage
