
from .azobject import AzSubObject
from .azobject import AzRoActionable


class StorageKey(AzRoActionable, AzSubObject):
    @classmethod
    def azobject_name_list(cls):
        return ['storage', 'account', 'keys']

    @classmethod
    def azobject_cmd_arg(cls):
        return '--name'

    @classmethod
    def get_parent_class(cls):
        from .storageaccount import StorageAccount
        return StorageAccount

    @classmethod
    def info_id(cls, info):
        return info.keyName

    @property
    def key_value(self):
        return self.info.value
