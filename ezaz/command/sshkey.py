
from .command import AzCommonActionCommand


class SshKeyCommand(AzCommonActionCommand):
    @classmethod
    def azclass(cls):
        from ..azobject.sshkey import SshKey
        return SshKey
