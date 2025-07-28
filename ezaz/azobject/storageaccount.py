
from .azobject import AzSubObject
from .azobject import AzSubObjectContainer
from .storagecontainer import StorageContainer
from .storagekey import StorageKey


class StorageAccount(AzSubObject, AzSubObjectContainer):
    @classmethod
    def azobject_name_list(cls):
        return ['storage', 'account']

    @classmethod
    def azobject_cmd_arg(cls):
        return '--name'

    @classmethod
    def azobject_subcmd_arg(cls):
        return '--account-name'

    @classmethod
    def get_azsubobject_classes(cls):
        return [StorageContainer, StorageKey]
