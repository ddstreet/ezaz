
from ..exception import NoAzObjectExists
from .azobject import AzRoActionable
from .azobject import AzSubObject


class Location(AzRoActionable, AzSubObject):
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
    def get_show_action_cmd(cls):
        return cls.get_cmd_base() + ['list-locations']

    @classmethod
    def get_parent_class(cls):
        from .subscription import Subscription
        return Subscription

    @classmethod
    def get_common_argconfigs(cls, is_parent=False):
        # We don't want the --subscription or --location params
        return []

    def _get_info(self, **opts):
        for info in super()._get_info(**opts):
            if info.name == self.azobject_id:
                return info
        raise NoAzObjectExists(self.azobject_text(), self.azobject_id)
