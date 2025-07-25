
from .command import AzObjectActionCommand


class SshKeyCommand(AzObjectActionCommand):
    @classmethod
    def azclass(cls):
        from ..azobject.sshkey import SshKey
        return SshKey
