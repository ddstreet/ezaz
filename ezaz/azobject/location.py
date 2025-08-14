
from ..exception import NoAzObjectExists
from .azobject import AzEmulateShowable
from .azobject import AzListable
from .azobject import AzSubObject


class Location(AzEmulateShowable, AzListable, AzSubObject):
    @classmethod
    def azobject_name_list(cls):
        return ['location']

    @classmethod
    def get_cmd_base(cls):
        return ['account']

    @classmethod
    def get_list_action_cmd(cls):
        return cls.get_cmd_base() + ['list-locations']

    @classmethod
    def get_parent_class(cls):
        from .subscription import Subscription
        return Subscription

    @classmethod
    def get_parent_common_argconfigs(cls):
        # We don't want the --subscription param
        return []
