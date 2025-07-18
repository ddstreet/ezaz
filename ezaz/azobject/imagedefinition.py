
from . import AzSubObject
from . import AzSubObjectContainer


class ImageDefinition(AzSubObject, AzSubObjectContainer()):
    @classmethod
    def subobject_name_list(cls):
        return ['image', 'definition']

    @classmethod
    def get_base_cmd(cls):
        return ['sig', 'image-definition']

    def get_my_cmd_args(self):
        return ['--gallery-image-definition', self.object_id]

    def get_my_create_cmd_args(self, **kwargs):
        return self.get_my_cmd_args(**kwargs) + ['--offer', kwargs.get('offer'),
                                                 '--os-type', kwargs.get('os_type'),
                                                 '--publisher', kwargs.get('publisher'),
                                                 '--sku', kwargs.get('sku')]
