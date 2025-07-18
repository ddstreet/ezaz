
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

    def get_my_cmd_args(self, **kwargs):
        return ['--resource-group', self.object_id]

    def get_my_create_cmd_args(self, **kwargs):
        location = self.required_arg_by_arg('location', 'create', **kwargs)
        return self.get_my_cmd_args(**kwargs) + ['--location', location]
