
from ..argutil import ArgConfig
from ..argutil import FlagArgConfig
from ..argutil import RequiredArgConfig
from .azobject import AzCommonActionable
from .azobject import AzSubObject
from .azobject import AzSubObjectContainer


class ResourceGroup(AzCommonActionable, AzSubObject, AzSubObjectContainer):
    @classmethod
    def azobject_name_list(cls):
        return ['resource', 'group']

    @classmethod
    def get_parent_class(cls):
        from .subscription import Subscription
        return Subscription

    @classmethod
    def get_child_classes(cls):
        from .imagegallery import ImageGallery
        from .sshkey import SshKey
        from .storageaccount import StorageAccount
        from .vm import VM
        return [ImageGallery, SshKey, StorageAccount, VM]

    @classmethod
    def get_cmd_base(cls):
        return ['group']

    @classmethod
    def get_create_action_argconfigs(cls):
        return [RequiredArgConfig('location', help='Location')]

    @classmethod
    def get_delete_action_argconfigs(cls):
        return [FlagArgConfig('no_wait', help='Do not wait for long-running tasks to finish'),
                FlagArgConfig('y', 'yes', help='Do not prompt for confirmation')]
