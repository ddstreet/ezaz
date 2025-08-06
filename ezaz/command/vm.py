
from ..azobject.vm import VM
from .command import AzSubObjectActionCommand
from .resourcegroup import ResourceGroupCommand


class VMCommand(AzSubObjectActionCommand):
    @classmethod
    def parent_command_cls(cls):
        return ResourceGroupCommand

    @classmethod
    def azclass(cls):
        return VM
