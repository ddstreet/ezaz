
from ..argutil import ChoicesArgConfig
from ..argutil import FlagArgConfig
from .azobject import AzEmulateShowable
from .azobject import AzListable
from .azobject import AzSubObject


class MarketplaceImageVersion(AzEmulateShowable, AzListable, AzSubObject):
    @classmethod
    def azobject_name_list(cls):
        return ['marketplace', 'image', 'version']

    @classmethod
    def get_cmd_base(cls):
        return ['vm', 'image']

    @classmethod
    def get_parent_class(cls):
        from .marketplaceimage import MarketplaceImage
        return MarketplaceImage

    @classmethod
    def get_list_action_cmd(cls):
        return cls.get_cmd_base() + ['list']

    @classmethod
    def get_list_action_argconfigs(cls):
        return [*super().get_list_action_argconfigs(),
                ChoicesArgConfig('architecture', choices=['Arm64', 'x64'], help='Architecture'),
                FlagArgConfig('all', default=True, hidden=True)]
