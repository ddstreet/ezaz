
from ..argutil import FlagArgConfig
from .azobject import AzCommonActionable
from .azobject import AzSubObject
from .azobject import AzSubObjectContainer
from .imagedefinition import ImageDefinition


class ImageGallery(AzCommonActionable, AzSubObject, AzSubObjectContainer):
    @classmethod
    def azobject_name_list(cls):
        return ['image', 'gallery']

    @classmethod
    def azobject_cmd_arg(cls):
        return '--gallery-name'

    @classmethod
    def get_azsubobject_classes(cls):
        return [ImageDefinition]

    @classmethod
    def get_cmd_base(cls):
        return ['sig']

    @classmethod
    def get_create_action_argconfigs(cls):
        return [FlagArgConfig('no_wait', help='Do not wait for long-running tasks to finish')]

    @classmethod
    def get_delete_action_argconfigs(cls):
        return [FlagArgConfig('no_wait', help='Do not wait for long-running tasks to finish')]
