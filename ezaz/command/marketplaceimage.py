
from .command import AzObjectActionCommand


class MarketplaceImageCommand(AzObjectActionCommand):
    @classmethod
    def azclass(cls):
        from ..azobject.marketplaceimage import MarketplaceImage
        return MarketplaceImage
