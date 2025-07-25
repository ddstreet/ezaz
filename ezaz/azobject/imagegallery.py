
from .azobject import AzSubObject
from .azobject import AzSubObjectContainer
from .imagedefinition import ImageDefinition


class ImageGallery(AzSubObject, AzSubObjectContainer):
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
    def get_base_cmd(cls):
        return ['sig']
