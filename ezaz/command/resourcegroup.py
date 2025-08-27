
from .command import AzCommonActionCommand


class ResourceGroupCommand(AzCommonActionCommand):
    @classmethod
    def azclass(cls):
        from ..azobject.resourcegroup import ResourceGroup
        return ResourceGroup

    @classmethod
    def aliases(cls):
        return ['group', 'rg']
