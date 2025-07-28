
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

    def _get_cmd_args(self, cmdname, opts):
        if cmdname == 'create':
            return self.optional_flag_arg('no_wait', opts)
        if cmdname == 'delete':
            return self.optional_flag_arg('no_wait', opts)
        return super()._get_cmd_args(cmdname, opts)
