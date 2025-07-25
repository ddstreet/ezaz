
from .azobject import AzEmulateShowable
from .azobject import AzListable
from .azobject import AzSubObjectContainer


class MarketplacePublisher(AzEmulateShowable, AzListable, AzSubObjectContainer):
    @classmethod
    def azobject_name_list(cls):
        return ['marketplace', 'publisher']

    @classmethod
    def get_cmd_base(cls):
        return ['vm', 'image']

    @classmethod
    def get_parent_class(cls):
        from .location import Location
        return Location

    @classmethod
    def get_child_classes(cls):
        from .marketplaceoffer import MarketplaceOffer
        return [MarketplaceOffer]

    @classmethod
    def get_self_id_argconfig_cmddest(cls, is_parent):
        return 'publisher'

    @classmethod
    def get_list_action_cmd(cls):
        return cls.get_cmd_base() + ['list-publishers']
