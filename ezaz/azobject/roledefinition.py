
from ..argutil import ArgConfig
from .azobject import AzRoActionable
from .azobject import AzSubObject


class RoleDefinition(AzRoActionable, AzSubObject):
    @classmethod
    def azobject_name_list(cls):
        return ['role', 'definition']

    @classmethod
    def get_parent_class(cls):
        from .subscription import Subscription
        return Subscription

    @classmethod
    def get_self_id_argconfig_dest(cls, is_parent):
        return 'name'

    @classmethod
    def get_show_action_argconfigs(cls):
        # Scope is hardcoded to the 'built-in' scope here, but it
        # could be any object (e.g. group, vm, etc)
        return [ArgConfig('scope', default='/', hidden=True)]
