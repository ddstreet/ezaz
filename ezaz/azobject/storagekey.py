
from .azobject import AzSubObject
from .azobject import AzSubObjectContainer
from .storageblob import StorageBlob


class StorageKey(AzSubObject):
    @classmethod
    def azobject_name_list(cls):
        return ['storage', 'account', 'keys']

    @classmethod
    def azobject_cmd_arg(cls):
        return '--name'

    @classmethod
    def info_id(cls, info):
        return info.keyName

    @classmethod
    def get_action_configmap(cls):
        return {}

    @property
    def key_value(self):
        return self.info.value
