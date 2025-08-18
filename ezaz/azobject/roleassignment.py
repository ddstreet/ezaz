
from .. import BUILT_IN_ROLES
from ..argutil import AzObjectArgConfig
from ..argutil import ChoiceMapArgConfig
from ..argutil import FlagArgConfig
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
    def get_cmd_base(cls):
        return ['role', 'assignment']

    @classmethod
    def get_list_action_argconfigs(cls):
        return [FlagArgConfig('all', default=True, hidden=True)]

    @classmethod
    def get_create_common_argconfigs(cls, is_parent=False):
        # Don't include our self id param for create action; it's auto-generated
        return [argconfig for argconfig in cls.get_common_argconfigs(is_parent=is_parent)
                if argconfig.dest != cls.get_self_id_argconfig_dest(is_parent=is_parent)]

    @classmethod
    def get_create_action_argconfigs(cls):
        from .resourcegroup import ResourceGroup
        from .user import User
        return [ChoiceMapArgConfig('role', choicemap=BUILT_IN_ROLES, required=True, help='Built-in role to assign'),
                AzObjectArgConfig('scope', azclass=ResourceGroup, cmd_attr='id', help='Scope to restrict the assignment to (currently restricted to resource group scope only)'),
                AzObjectArgConfig('assignee', azclass=User, help='User to assign to role')]
