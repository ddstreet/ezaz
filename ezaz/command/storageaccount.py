
from .command import AzObjectActionCommand


class StorageAccountCommand(AzObjectActionCommand):
    @classmethod
    def azclass(cls):
        from ..azobject.storageaccount import StorageAccount
        return StorageAccount
