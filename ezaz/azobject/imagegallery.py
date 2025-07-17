
from . import AzSubObject
from . import AzSubObjectContainer
from .imagedefinition import ImageDefinition


class ImageGallery(AzSubObject, AzSubObjectContainer([ImageDefinition])):
    @classmethod
    def subobject_name_list(cls):
        return ['image', 'gallery']

    @classmethod
    def get_base_cmd(cls):
        return ['sig']

    def get_my_cmd_opts(self, **kwargs):
        return ['--gallery-name', self.object_id]
