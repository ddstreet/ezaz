
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
    def get_base_cmd(cls):
        return ['group']

    def get_my_subcmd_opts(self, **kwargs):
        return ['--resource-group', self.object_id]

    def get_my_create_cmd_opts(self, **kwargs):
        location = self._required_param('location', f'The --create parameter requires --location', **kwargs)
        return self.get_my_subcmd_opts() + ['--location', location]
