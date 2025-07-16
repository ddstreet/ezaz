
from . import AzSubObject
from . import AzSubObjectContainer
from .storagecontainer import StorageContainer


class StorageAccount(AzSubObject, AzSubObjectContainer([StorageContainer])):
    @classmethod
    def subobject_name_list(cls):
        return ['storage', 'account']

    @classmethod
    def get_show_cmd(cls):
        return ['storage', 'account', 'show']

    @classmethod
    def get_create_cmd(self):
        raise NotCreatable()

    @classmethod
    def get_delete_cmd(self):
        raise NotDeletable()

    @classmethod
    def get_list_cmd(cls):
        return ['storage', 'account', 'list']

    def get_cmd_opts(self):
        return super().get_subcmd_opts() + ['--name', self.object_id]

    def get_subcmd_opts(self):
        return super().get_subcmd_opts() + ['--account-name', self.object_id]
