
from . import AzSubObject
from . import AzSubObjectContainer


class ImageDefinition(AzSubObject, AzSubObjectContainer()):
    @classmethod
    def subobject_name_list(cls):
        return ['image', 'definition']

    @classmethod
    def get_base_cmd(cls):
        return ['sig', 'image-definition']

    def get_my_cmd_args(self, opts):
        return {'--gallery-image-definition': self.object_id}

    def get_my_create_cmd_args(self, opts):
        args = {'--offer': self.required_arg('offer', 'create', opts),
                '--os-type': self.required_arg('os_type', 'create', opts),
                '--publisher': self.required_arg('publisher', 'create', opts),
                '--sku': self.required_arg('sku', 'create', opts)}
        return self.get_my_cmd_args(opts) | args
