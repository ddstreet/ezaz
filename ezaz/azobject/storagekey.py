
from .azobject import AzEmulateShowable
from .azobject import AzListable
from .azobject import AzSubObject


class StorageKey(AzEmulateShowable, AzListable, AzSubObject):
    @classmethod
    def azobject_name_list(cls):
        return ['storage', 'key']

    @classmethod
    def get_cmd_base(cls):
        return ['storage', 'account', 'keys']

    @classmethod
    def get_parent_class(cls):
        from .storageaccount import StorageAccount
        return StorageAccount
