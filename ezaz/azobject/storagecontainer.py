
from contextlib import suppress

from ..argutil import ArgConfig
from ..argutil import ArgMap
from ..argutil import AzObjectArgConfig
from ..argutil import AzObjectDefaultId
from ..argutil import ChoicesArgConfig
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
        return (super().get_common_argconfigs(is_parent=is_parent) +
                [ArgConfig('storage_key', dest='account_key', hidden=True),
                 ChoicesArgConfig('auth_mode', choices=['key', 'login'], hidden=True)])

    def get_argconfig_default_values(self, is_parent=False):
        return ArgMap(super().get_argconfig_default_values(is_parent=is_parent),
                      auth_mode=self.auth_mode,
                      account_key=self.account_key)

    @property
    def auth_mode(self):
        return 'key' if self.parent.allow_shared_key_access else 'login'

    @property
    def account_key(self):
        from .storagekey import StorageKey
        if not self.parent.allow_shared_key_access:
            return None
        try:
            key = self.parent.get_default_child(StorageKey.azobject_name())
        except DefaultConfigNotFound as dcnf:
            try:
                key = self.parent.get_children(StorageKey.azobject_name())[0]
            except IndexError:
                raise dcnf
        return key.info().value
