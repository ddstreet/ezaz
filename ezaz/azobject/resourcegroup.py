
from .azobject import AzSubObject
from .azobject import AzSubObjectContainer
from .imagegallery import ImageGallery
from .sshkey import SshKey
from .storageaccount import StorageAccount
from .vm import VM


class ResourceGroup(AzSubObject, AzSubObjectContainer):
    @classmethod
    def subobject_name_list(cls):
        return ['resource', 'group']

    @classmethod
    def get_azsubobject_classes(cls):
        return [ImageGallery, SshKey, StorageAccount, VM]

    @classmethod
    def get_base_cmd(cls):
        return ['group']

    def get_my_cmd_args(self, opts):
        return {'--resource-group': self.object_id}

    def _get_my_create_cmd_args(self, opts):
        return self.required_arg('location', opts, 'create')
