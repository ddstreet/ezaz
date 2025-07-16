
from . import AzSubObject
from . import AzSubObjectContainer
from .imagegallery import ImageGallery
from .sshkey import SshKey
from .storageaccount import StorageAccount
from .vm import VM


class ResourceGroup(AzSubObject, AzSubObjectContainer([ImageGallery, SshKey, StorageAccount, VM])):
    @classmethod
    def subobject_name_list(cls):
        return ['resource', 'group']

    @classmethod
    def get_show_cmd(cls):
        return ['group', 'show']

    @classmethod
    def get_create_cmd(self):
        return ['group', 'create']

    @classmethod
    def get_delete_cmd(self):
        raise NotDeletable()

    @classmethod
    def get_list_cmd(cls):
        return ['group', 'list']

    def get_cmd_opts(self):
        return self.get_subcmd_opts()

    def get_subcmd_opts(self):
        return super().get_subcmd_opts() + ['--resource-group', self.object_id]
