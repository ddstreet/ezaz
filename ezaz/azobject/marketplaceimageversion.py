
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
                ChoicesArgConfig('architecture', choices=['Arm64', 'x64'], noncmd=True, help='Architecture'),
                FlagArgConfig('all', default=True, hidden=True)]

    def _list_filter(self, infos, opts):
        # We manually filter for architecture, so we can cache the full list
        architecture = opts.get('architecture')
        # azcli is broken, and returns partial matches for these fields, so we have to filter these manually
        image = self.parent
        offer = image.parent
        publisher = offer.parent
        infos = [info for info in infos
                 if all((info.publisher == publisher.azobject_id,
                         info.offer == offer.azobject_id,
                         info.sku == image.azobject_id,
                         not architecture or info.architecture == architecture))]
        return infos
