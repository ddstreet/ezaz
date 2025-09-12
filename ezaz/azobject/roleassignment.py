
from ..argutil import AzObjectArgConfig
from ..argutil import ChoiceMapArgConfig
from ..argutil import FlagArgConfig
from ..argutil import ExclusiveGroupArgConfig
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
    def get_create_action_azobject_id_argconfigs(cls):
        # Don't include our self id param for create action; it's auto-generated
        return [argconfig for argconfig in super().get_create_action_azobject_id_argconfigs()
                if argconfig.cmddest != cls.get_self_id_argconfig_cmddest(is_parent=False)]

    @classmethod
    def get_create_action_get_instance(cls):
        return cls.get_null_instance

    @classmethod
    def get_create_action_argconfigs(cls):
        from .resourcegroup import ResourceGroup
        from .roledefinition import RoleDefinition
        from .user import User
        return [ExclusiveGroupArgConfig(*ResourceGroup.get_descendant_azobject_id_argconfigs(include_self=True,
                                                                                             cmddest=None,
                                                                                             cmdattr='id',
                                                                                             help='Restrict assignment to specified {azobject_text}'),
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

    @classmethod
    def is_create_id_required(cls):
        return False

    def create_pre(self, opts):
        return None

    def create_invalidate_cache(self, tag=None):
        self.cache.invalidate_info_list(tag=tag)
