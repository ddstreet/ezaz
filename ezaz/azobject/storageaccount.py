
from ..argutil import YesFlagArgConfig
from .azobject import AzCommonActionable
from .azobject import AzSubObject
from .azobject import AzSubObjectContainer


class StorageAccount(AzCommonActionable, AzSubObject, AzSubObjectContainer):
    @classmethod
    def azobject_name_list(cls):
        return ['storage', 'account']

    @classmethod
    def get_parent_class(cls):
        from .resourcegroup import ResourceGroup
        return ResourceGroup

    @classmethod
    def get_child_classes(cls):
        from .storagecontainer import StorageContainer
        from .storagekey import StorageKey
        return [StorageContainer, StorageKey]

    @classmethod
    def get_self_id_argconfig_dest(cls, is_parent):
        return 'account_name' if is_parent else 'name'

    @classmethod
    def get_delete_action_argconfigs(cls):
        return [YesFlagArgConfig()]
