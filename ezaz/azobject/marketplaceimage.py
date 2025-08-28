
from .azobject import AzEmulateShowable
from .azobject import AzListable
from .azobject import AzSubObjectContainer


class MarketplaceImage(AzEmulateShowable, AzListable, AzSubObjectContainer):
    @classmethod
    def azobject_name_list(cls):
        return ['marketplace', 'image']

    @classmethod
    def get_cmd_base(cls):
        return ['vm', 'image']

    @classmethod
    def get_parent_class(cls):
        from .marketplaceoffer import MarketplaceOffer
        return MarketplaceOffer

    @classmethod
    def get_child_classes(cls):
        from .marketplaceimageversion import MarketplaceImageVersion
        return [MarketplaceImageVersion]

    @classmethod
    def get_self_id_argconfig_cmddest(cls, is_parent):
        return 'sku'

    @classmethod
    def get_list_action_cmd(cls):
        return cls.get_cmd_base() + ['list-skus']
