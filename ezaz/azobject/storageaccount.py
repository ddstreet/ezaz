
from .azobject import AzSubObject
from .azobject import AzSubObjectContainer
from .storagecontainer import StorageContainer


class StorageAccount(AzSubObject, AzSubObjectContainer):
    @classmethod
    def subobject_name_list(cls):
        return ['storage', 'account']

    @classmethod
    def get_azsubobject_classes(cls):
        return [StorageContainer]

    def get_my_cmd_args(self, opts):
        return {'--name': self.object_id}

    def get_my_subcmd_args(self, opts):
        return {'--account-name': self.object_id}
