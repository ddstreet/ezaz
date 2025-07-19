
from . import AzSubObject
from . import AzSubObjectContainer
from . import AzSubObjectContainerChildren
from .imagegallery import ImageGallery
from .sshkey import SshKey
from .storageaccount import StorageAccount
from .vm import VM


class ResourceGroup(AzSubObject, AzSubObjectContainer, *AzSubObjectContainerChildren([ImageGallery, SshKey, StorageAccount, VM])):
    @classmethod
    def subobject_name_list(cls):
        return ['resource', 'group']

    @classmethod
    def get_base_cmd(cls):
        return ['group']

    def get_my_cmd_args(self, opts):
        return {'--resource-group': self.object_id}

    def get_my_create_cmd_args(self, opts):
        location = self.required_arg('location', 'create', opts)
        return self.get_my_cmd_args(opts) | {'--location': location}
