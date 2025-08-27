
from .command import AzCommonActionCommand


class VMCommand(AzCommonActionCommand):
    @classmethod
    def azclass(cls):
        from ..azobject.vm import VM
        return VM
