
from ..argutil import ArgConfig
from ..argutil import ChoicesArgConfig
from ..argutil import FlagArgConfig
from .azobject import AzCommonActionable
from .azobject import AzFilterer
from .azobject import AzSubObject


class ImageDefinition(AzCommonActionable, AzFilterer, AzSubObject):
    @classmethod
    def azobject_name_list(cls):
        return ['image', 'definition']

    @classmethod
    def get_cmd_base(cls):
        return ['sig', 'image-definition']

    @classmethod
    def get_parent_class(cls):
        from .imagegallery import ImageGallery
        return ImageGallery

    @classmethod
    def get_self_id_argconfig_dest(cls, is_parent):
        return 'gallery_image_definition'

    @classmethod
    def get_create_action_argconfigs(cls):
        return [ArgConfig('publisher', required=True, help='Publisher'),
                ArgConfig('offer', required=True, help='Offer'),
                ArgConfig('sku', required=True, help='SKU'),
                ChoicesArgConfig('os_type', choices=['linux', 'windows'], default='linux', help='OS type (default: linux)'),
                ChoicesArgConfig('architecture', choices=['x64', 'Arm64'], default='x64', help='CPU architecture (default: x64))'),
                ChoicesArgConfig('hyper_v_generation', choices=['V1', 'V2'], default='V2', hidden=True),
                ArgConfig('features', default='SecurityType=TrustedLaunchSupported', hidden=True)]

    @classmethod
    def get_delete_action_argconfigs(cls):
        return [FlagArgConfig('no_wait', help='Do not wait for long-running tasks to finish')]
