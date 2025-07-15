
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
    def show_cmd(cls):
        return ['group', 'show']

    @classmethod
    def list_cmd(cls):
        return ['group', 'list']

    def cmd_opts(self):
        return self.subcmd_opts()

    def subcmd_opts(self):
        return super().subcmd_opts() + ['--resource-group', self.object_id]
