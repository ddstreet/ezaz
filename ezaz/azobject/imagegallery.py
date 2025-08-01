
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
    def get_cmd_base(cls, action):
        return ['sig']

    @classmethod
    def get_action_configmap(cls):
        return {}

    def get_create_action_cmd_args(self, action, opts):
        return self.optional_flag_arg('no_wait', opts)

    def get_delete_action_cmd_args(self, action, opts):
        return self.optional_flag_arg('no_wait', opts)
