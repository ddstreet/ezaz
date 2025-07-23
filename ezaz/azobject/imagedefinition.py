
from .azobject import AzSubObject


class ImageDefinition(AzSubObject):
    @classmethod
    def azobject_name_list(cls):
        return ['image', 'definition']

    @classmethod
    def azobject_cmd_arg(cls):
        return '--gallery-image-definition'

    @classmethod
    def get_base_cmd(cls):
        return ['sig', 'image-definition']

    def _get_create_cmd_args(self, opts):
        return self.required_args_all(['offer', 'os_type', 'publisher', 'sku'], opts, 'create')
