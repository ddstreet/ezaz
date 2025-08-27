
from .azobject import AzEmulateShowable
from .azobject import AzListable
from .azobject import AzSubObject


class Sku(AzEmulateShowable, AzListable, AzSubObject):
    @classmethod
    def azobject_name_list(cls):
        return ['sku']

    @classmethod
    def get_cmd_base(cls):
        return ['vm']

    @classmethod
    def get_parent_class(cls):
        from .subscription import Subscription
        return Subscription

    @classmethod
    def get_list_action_cmd(cls):
        return cls.get_cmd_base() + ['list-skus']

    @classmethod
    def get_list_action_argconfigs(cls):
        from .location import Location
        return [*super().get_list_action_argconfigs(),
                *Location.get_self_id_argconfigs(is_parent=True)]
