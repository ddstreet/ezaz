
from ..argutil import AzObjectArgConfig
from ..argutil import GroupArgConfig
from .azobject import AzSubObjectContainer
from .azobject import AzListable
from .azobject import AzShowable


class Subscription(AzShowable, AzListable, AzSubObjectContainer):
    @classmethod
    def azobject_name_list(cls):
        return ['subscription']

    @classmethod
    def get_cmd_base(cls):
        return ['account']

    @classmethod
    def get_parent_class(cls):
        from .account import Account
        return Account

    @classmethod
    def get_child_classes(cls):
        from .location import Location
        from .resourcegroup import ResourceGroup
        from .roleassignment import RoleAssignment
        from .roledefinition import RoleDefinition
        from .sku import Sku
        return [Location, ResourceGroup, RoleAssignment, RoleDefinition, Sku]

    @classmethod
    def get_self_id_argconfigs(cls, is_parent=False, help=None, **kwargs):
        return [GroupArgConfig(AzObjectArgConfig('subscription',
                                                 azclass=cls,
                                                 help=help or f'Use the specified {cls.azobject_text()}, instead of the default',
                                                 **kwargs),
                               AzObjectArgConfig('subscription_name',
                                                 azclass=cls,
                                                 infoattr='name',
                                                 help=help or f'Use the specified {cls.azobject_text()}, instead of the default',
                                                 **kwargs),
                               cmddest=cls.get_self_id_argconfig_cmddest(is_parent=is_parent))]
