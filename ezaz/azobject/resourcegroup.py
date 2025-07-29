
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
    def get_base_cmd(cls):
        return ['group']

    def _get_cmd_args(self, cmdname, opts):
        if cmdname == 'create':
            return self.required_arg('location', opts, 'create')
        if cmdname == 'delete':
            return self.optional_flag_args(['yes', 'no_wait'], opts)
        return super()._get_cmd_args(cmdname, opts)
