
from contextlib import suppress

from ..argutil import ArgConfig
from ..argutil import ArgMap
from .azobject import AzCommonActionable
from .azobject import AzSubObject
from .azobject import AzSubObjectContainer
from .storagekey import StorageKey


class StorageContainer(AzCommonActionable, AzSubObject, AzSubObjectContainer):
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
    def get_common_argconfigs(self, is_parent=False):
        return [*filter(lambda a: a.dest != 'resource_group', super().get_common_argconfigs(is_parent=is_parent)),
                ArgConfig('account_key', hidden=True),
                ArgConfig('auth_mode', default='key', hidden=True)]

    def get_argconfig_default_values(self, is_parent=False):
        return ArgMap(super().get_argconfig_default_values(is_parent=is_parent),
                      account_key=self.storage_account_key)

    @property
    def storage_account_key(self):
        keys = self.parent.get_children(StorageKey.azobject_name())
        with suppress(IndexError):
            return keys[0].key_value
        return None

