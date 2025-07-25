
from .command import AzObjectActionCommand


class SkuCommand(AzObjectActionCommand):
    @classmethod
    def azclass(cls):
        from ..azobject.sku import Sku
        return Sku
