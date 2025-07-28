
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

    def _get_cmd_args(self, cmdname, opts):
        if cmdname == 'delete':
            return self.optional_flag_arg('yes', opts)
        return super()._get_cmd_args(cmdname, opts)
