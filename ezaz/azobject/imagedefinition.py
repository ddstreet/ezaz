
from .azobject import AzSubObject


class ImageDefinition(AzSubObject):
    @classmethod
    def subobject_name_list(cls):
        return ['image', 'definition']

    @classmethod
    def get_base_cmd(cls):
        return ['sig', 'image-definition']

    def get_my_cmd_args(self, opts):
        return {'--gallery-image-definition': self.object_id}

    def _get_my_create_cmd_args(self, opts):
        return self.required_args_all(['offer', 'os_type', 'publisher', 'sku'], opts, 'create')
