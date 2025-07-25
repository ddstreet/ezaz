
from .command import AzObjectActionCommand


class ResourceGroupCommand(AzObjectActionCommand):
    @classmethod
    def azclass(cls):
        from ..azobject.resourcegroup import ResourceGroup
        return ResourceGroup

    @classmethod
    def aliases(cls):
        return ['group', 'rg']
