
from contextlib import suppress

from ..argutil import ArgConfig
from ..argutil import ArgMap
from ..argutil import AzObjectArgConfig
from ..argutil import AzObjectDefaultId
from .azobject import AzCommonActionable
from .azobject import AzFilterer
from .azobject import AzSubObject
from .azobject import AzSubObjectContainer


class StorageContainer(AzCommonActionable, AzFilterer, AzSubObject, AzSubObjectContainer):
    @classmethod
    def azobject_name_list(cls):
        return ['storage', 'container']

    @classmethod
    def get_parent_class(cls):
        from .storageaccount import StorageAccount
        return StorageAccount

    @classmethod
    def get_child_classes(cls):
        from .storageblob import StorageBlob
        return [StorageBlob]

    @classmethod
    def get_self_id_argconfig_dest(cls, is_parent):
        return 'container_name' if is_parent else 'name'

    @classmethod
    def get_parent_common_argconfigs(self):
        return [*filter(lambda a: a.dest != 'resource_group', super().get_parent_common_argconfigs())]

    @classmethod
    def get_common_argconfigs(self, is_parent=False):
        from .storagekey import StorageKey
        return (super().get_common_argconfigs(is_parent=is_parent) +
                [AzObjectArgConfig('storage_key', azclass=StorageKey, cmd_attr='value', dest='account_key', hidden=True),
                 ArgConfig('auth_mode', default='key', hidden=True)])
