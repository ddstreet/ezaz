
from ..argutil import AzObjectArgConfig
from ..argutil import ChoiceMapArgConfig
from ..argutil import FlagArgConfig
from ..argutil import GroupArgConfig
from .azobject import AzCreatable
from .azobject import AzEmulateShowable
from .azobject import AzSubObject


class RoleAssignment(AzEmulateShowable, AzCreatable, AzSubObject):
    @classmethod
    def azobject_name_list(cls):
        return ['role', 'assignment']

    @classmethod
    def get_parent_class(cls):
        from .subscription import Subscription
        return Subscription

    @classmethod
    def get_list_action_argconfigs(cls):
        return [FlagArgConfig('all', default=True, hidden=True)]

    @classmethod
    def get_create_common_argconfigs(cls, is_parent=False):
        # Don't include our self id param for create action; it's auto-generated
        return [argconfig for argconfig in cls.get_common_argconfigs(is_parent=is_parent)
                if argconfig.cmddest != cls.get_self_id_argconfig_cmddest(is_parent=is_parent)]

    @classmethod
    def get_scope_group_argconfigs(cls):
        from .resourcegroup import ResourceGroup
        from .storageaccount import StorageAccount
        from .storagecontainer import StorageContainer
        from .storageblob import StorageBlob
        from .imagegallery import ImageGallery
        from .imagedefinition import ImageDefinition
        from .imageversion import ImageVersion
        from .vm import VM
        for azclass in [ResourceGroup, StorageAccount, StorageContainer, StorageBlob, ImageGallery, ImageDefinition, ImageVersion, VM]:
            yield AzObjectArgConfig(azclass.azobject_name(),
                                    azclass=azclass,
                                    cmdattr='id',
                                    help='Restrict assignment to specified {azclass.azobject_text()}')

    @classmethod
    def get_create_action_argconfigs(cls):
        from .roledefinition import RoleDefinition
        from .user import User
        return [GroupArgConfig(*cls.get_scope_group_argconfigs(),
                               required=True,
                               cmddest='scope'),
                AzObjectArgConfig('role',
                                  azclass=RoleDefinition,
                                  infoattr='roleName',
                                  cmdattr='name',
                                  nodefault=True,
                                  required=True,
                                  help='Role to assign'),
                AzObjectArgConfig('assignee',
                                  azclass=User,
                                  help='User to assign to role')]
