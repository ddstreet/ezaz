
from .command import StorageAccountSubCommand


class StorageContainerCommand(StorageAccountSubCommand):
    @classmethod
    def _cls_type_list(cls):
        return ['storage', 'container']

    def _show(self, storage_containter):
        info = storage_containter.info
        msg = info.name
        if self.verbose:
            msg += f' (location: {info.location})'
        print(msg)

