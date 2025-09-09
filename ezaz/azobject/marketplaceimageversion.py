
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

    @property
    def id_list_supported(self):
        return False

    def list_filter(self, infolist, opts):
        # We manually filter for architecture, so we can cache the full list
        architecture = opts.get('architecture')
        if architecture:
            return [info for info in infolist if info.architecture == architecture]
        return super().list_filter(infolist, opts)

    def list_post(self, infolist, opts):
        # azcli is broken, and returns partial matches for these
        # fields, so we have to filter these manually, and *before*
        # writing to cache
        image = self.parent
        offer = image.parent
        publisher = offer.parent
        infolist = [info for info in infolist if all((info.publisher == publisher.azobject_id,
                                                      info.offer == offer.azobject_id,
                                                      info.sku == image.azobject_id))]
        return super().list_post(infolist, opts)
