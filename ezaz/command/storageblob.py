
from .command import AzSubObjectActionCommand


class StorageBlobCommand(AzSubObjectActionCommand):
    @classmethod
    def parent_command_cls(cls):
        from .storagecontainer import StorageContainerCommand
        return StorageContainerCommand

    @classmethod
    def azclass(cls):
        from ..azobject.storageblob import StorageBlob
        return StorageBlob

    @property
    def azobject_default_id(self):
        if self.action in ['create']:
            if self.options.file:
                return self.options.file
            else:
                raise RequiredArgumentGroup([self.azobject_name(), 'file'], 'create')
        return super().azobject_default_id
