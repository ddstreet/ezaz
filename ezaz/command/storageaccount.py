
from .command import AzCommonActionCommand


class StorageAccountCommand(AzCommonActionCommand):
    @classmethod
    def azclass(cls):
        from ..azobject.storageaccount import StorageAccount
        return StorageAccount
