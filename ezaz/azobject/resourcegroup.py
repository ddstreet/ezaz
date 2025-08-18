
from ..argutil import ArgConfig
from ..argutil import AzObjectArgConfig
from ..argutil import BoolArgConfig
from ..argutil import NoWaitFlagArgConfig
from ..argutil import YesFlagArgConfig
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
        from .location import Location
        return [AzObjectArgConfig('location', azclass=Location, help='Location'),
                BoolArgConfig('no_rbac', noncmd=True, help='Do not add RBAC owner/contributor roles for the signed in user')]

    @classmethod
    def get_delete_action_argconfigs(cls):
        return [NoWaitFlagArgConfig(), YesFlagArgConfig()]

    def create(self, no_rbac=False, **opts):
        super().create(**opts)
        if no_rbac:
            return

        # Add owner and contributor RBAC for the signed-in user
        from .roleassignment import RoleAssignment
        roleassignment = RoleAssignment.create_from_opts(role_assignment='NONEXISTENT', **opts)
        roleassignment.create(role='owner', scope=self.azobject_id, **opts)
        roleassignment.create(role='contributor', scope=self.azobject_id, **opts)
