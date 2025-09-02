
from .azobject import AzEmulateShowable
from .azobject import AzListable
from .azobject import AzSubObjectContainer


class Location(AzEmulateShowable, AzListable, AzSubObjectContainer):
    @classmethod
    def azobject_name_list(cls):
        return ['location']

    @classmethod
    def get_cmd_base(cls):
        return ['account']

    @classmethod
    def get_parent_class(cls):
        from .subscription import Subscription
        return Subscription

    @classmethod
    def get_child_classes(cls):
        from .marketplacepublisher import MarketplacePublisher
        return [MarketplacePublisher]

    @classmethod
    def get_list_action_cmd(cls):
        return cls.get_cmd_base() + ['list-locations']

    @classmethod
    def get_list_action_azobject_id_argconfigs(cls):
        from .subscription import Subscription
        # Don't include our subscription id param for list action
        return [argconfig for argconfig in super().get_list_action_azobject_id_argconfigs()
                if argconfig.cmddest != Subscription.get_self_id_argconfig_cmddest(is_parent=True)]
