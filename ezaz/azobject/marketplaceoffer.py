
from .azobject import AzEmulateShowable
from .azobject import AzListable
from .azobject import AzSubObjectContainer


class MarketplaceOffer(AzEmulateShowable, AzListable, AzSubObjectContainer):
    @classmethod
    def azobject_name_list(cls):
        return ['marketplace', 'offer']

    @classmethod
    def get_cmd_base(cls):
        return ['vm', 'image']

    @classmethod
    def get_parent_class(cls):
        from .marketplacepublisher import MarketplacePublisher
        return MarketplacePublisher

    @classmethod
    def get_child_classes(cls):
        from .marketplaceimage import MarketplaceImage
        return [MarketplaceImage]

    @classmethod
    def get_self_id_argconfig_cmddest(cls, is_parent):
        return 'offer'

    @classmethod
    def get_list_action_cmd(cls):
        return cls.get_cmd_base() + ['list-offers']
