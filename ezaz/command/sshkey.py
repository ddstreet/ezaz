
from pathlib import Path

from .command import AzSubObjectActionCommand


class SshKeyCommand(AzSubObjectActionCommand):
    @classmethod
    def parent_command_cls(cls):
        from .resourcegroup import ResourceGroupCommand
        return ResourceGroupCommand

    @classmethod
    def azclass(cls):
        from ..azobject.sshkey import SshKey
        return SshKey
