
from .azobject import AzSubObject
from .azobject import AzSubObjectContainer
from .storagecontainer import StorageContainer


class StorageAccount(AzSubObject, AzSubObjectContainer):
    @classmethod
    def azobject_name_list(cls):
        return ['storage', 'account']

    @classmethod
    def azobject_arg(cls):
        return '--name'

    @classmethod
    def get_azsubobject_classes(cls):
        return [StorageContainer]

    def get_my_subcmd_args(self, opts):
        return {'--account-name': self.object_id}
