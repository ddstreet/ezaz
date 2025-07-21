
from .azobject import AzSubObject
from .azobject import AzSubObjectContainer
from .imagedefinition import ImageDefinition


class ImageGallery(AzSubObject, AzSubObjectContainer):
    @classmethod
    def subobject_name_list(cls):
        return ['image', 'gallery']

    @classmethod
    def get_azsubobject_classes(cls):
        return [ImageDefinition]

    @classmethod
    def get_base_cmd(cls):
        return ['sig']

    def get_my_cmd_args(self, opts):
        return {'--gallery-name': self.object_id}
