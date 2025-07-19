
from . import AzSubObject
from . import AzSubObjectContainer
from . import AzSubObjectContainerChildren
from .storagecontainer import StorageContainer


class StorageAccount(AzSubObject, AzSubObjectContainer, *AzSubObjectContainerChildren([StorageContainer])):
    @classmethod
    def subobject_name_list(cls):
        return ['storage', 'account']

    def get_my_cmd_args(self, opts):
        return {'--name': self.object_id}

    def get_my_subcmd_args(self, opts):
        return {'--account-name': self.object_id}
