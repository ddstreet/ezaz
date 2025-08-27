
from .command import AzCommonActionCommand


class SkuCommand(AzCommonActionCommand):
    @classmethod
    def azclass(cls):
        from ..azobject.sku import Sku
        return Sku
