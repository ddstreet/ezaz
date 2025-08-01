
from ..argutil import ArgConfig
from ..argutil import FlagArgConfig
from ..argutil import RequiredArgConfig
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
    def get_cmd_base(cls):
        return ['group']

    @classmethod
    def get_create_action_argconfigs(cls):
        return [RequiredArgConfig('location', help='Location'),
                FlagArgConfig('no_wait', help='Do not wait for long-running tasks to finish'),
                FlagArgConfig('y', 'yes', help='Do not prompt for confirmation')]
