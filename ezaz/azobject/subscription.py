
from .azobject import AzSubObjectContainer
from .azobject import AzDefaultable
from .azobject import AzListable
from .azobject import AzShowable


class Subscription(AzShowable, AzListable, AzDefaultable, AzSubObjectContainer):
    @classmethod
    def azobject_name_list(cls):
        return ['subscription']

    @classmethod
    def info_id(cls, info):
        return info.id

    @classmethod
    def get_parent_class(cls):
        from .account import Account
        return Account

    @classmethod
    def get_child_classes(cls):
        from .location import Location
        from .resourcegroup import ResourceGroup
        from .roleassignment import RoleAssignment
        return [ResourceGroup, RoleAssignment, Location]

    @classmethod
    def get_cmd_base(cls):
        return ['account']
