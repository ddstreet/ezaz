
from .command import AzCommonActionCommand


class VMCommand(AzCommonActionCommand):
    @classmethod
    def parent_command_cls(cls):
        from .resourcegroup import ResourceGroupCommand
        return ResourceGroupCommand

    @classmethod
    def azclass(cls):
        from ..azobject.vm import VM
        return VM
