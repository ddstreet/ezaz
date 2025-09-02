
from contextlib import suppress

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
        from .user import User
        return User

    @classmethod
    def get_child_classes(cls):
        from .location import Location
        from .resourcegroup import ResourceGroup
        from .roleassignment import RoleAssignment
        from .roledefinition import RoleDefinition
        from .sku import Sku
        return [Location, ResourceGroup, RoleAssignment, RoleDefinition, Sku]

    @classmethod
    def get_action_configs(cls):
        return [*super().get_action_configs(),
                cls.make_action_config('get_current',
                                       az='info',
                                       cmd=cls.get_cmd_base() + ['show'],
                                       common_argconfigs=[],
                                       get_instance=cls.get_null_instance,
                                       description='Get the current subscription'),
                cls.make_action_config('set_current',
                                       cmd=cls.get_cmd_base() + ['set'],
                                       description='Set the current subscription')]

    def get_current(self, **opts):
        return self.do_action_config_instance_action('get_current', opts)

    def set_current(self, **opts):
        self.do_action_config_instance_action('set_current', opts)
