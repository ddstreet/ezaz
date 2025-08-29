
from .command import AzObjectActionCommand


class VMCommand(AzObjectActionCommand):
    @classmethod
    def azclass(cls):
        from ..azobject.vm import VM
        return VM
