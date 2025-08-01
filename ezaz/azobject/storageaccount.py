
from .azobject import AzCommonActionable
from .azobject import AzSubObject
from .azobject import AzSubObjectContainer
from .storagecontainer import StorageContainer
from .storagekey import StorageKey


class StorageAccount(AzCommonActionable, AzSubObject, AzSubObjectContainer):
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

    @classmethod
    def get_action_configmap(cls):
        return {}

    def get_delete_action_cmd_args(self, action, opts):
        return self.optional_flag_arg('yes', opts)
