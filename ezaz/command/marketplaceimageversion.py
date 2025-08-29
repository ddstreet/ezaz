
from .command import AzObjectActionCommand


class MarketplaceImageVersionCommand(AzObjectActionCommand):
    @classmethod
    def azclass(cls):
        from ..azobject.marketplaceimageversion import MarketplaceImageVersion
        return MarketplaceImageVersion
