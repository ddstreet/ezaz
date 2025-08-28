
from .command import AzCommonActionCommand


class MarketplaceImageVersionCommand(AzCommonActionCommand):
    @classmethod
    def azclass(cls):
        from ..azobject.marketplaceimageversion import MarketplaceImageVersion
        return MarketplaceImageVersion
