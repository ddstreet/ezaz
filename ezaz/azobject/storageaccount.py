
from . import AzSubObject
from . import AzSubObjectContainer
from .storagecontainer import StorageContainer


class StorageAccount(AzSubObject, AzSubObjectContainer([StorageContainer])):
    @classmethod
    def subobject_name_list(cls):
        return ['storage', 'account']

    @classmethod
    def show_cmd(cls):
        return ['storage', 'account', 'show']

    @classmethod
    def list_cmd(cls):
        return ['storage', 'account', 'list']

    def cmd_opts(self):
        return super().subcmd_opts() + ['--name', self.object_id]

    def subcmd_opts(self):
        return super().subcmd_opts() + ['--account-name', self.object_id]
