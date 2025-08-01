
from .azobject import AzCommonActionable
from .azobject import AzSubObject
from .azobject import AzSubObjectContainer
from .imagegallery import ImageGallery
from .sshkey import SshKey
from .storageaccount import StorageAccount
from .vm import VM


class ResourceGroup(AzCommonActionable, AzSubObject, AzSubObjectContainer):
    @classmethod
    def azobject_name_list(cls):
        return ['resource', 'group']

    @classmethod
    def get_azsubobject_classes(cls):
        return [ImageGallery, SshKey, StorageAccount, VM]

    @classmethod
    def get_cmd_base(cls, action):
        return ['group']

    @classmethod
    def get_action_configmap(cls):
        return {}

    def get_create_action_cmd_args(self, action, opts):
        return self.required_arg('location', opts, 'create')

    def get_create_action_cmd_args(self, action, opts):
        return self.optional_flag_args(['yes', 'no_wait'], opts)
