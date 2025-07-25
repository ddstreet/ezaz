
from ..argutil import NoWaitBoolArgConfig
from .azobject import AzCommonActionable
from .azobject import AzSubObject
from .azobject import AzFilterer
from .azobject import AzSubObjectContainer


class ImageGallery(AzCommonActionable, AzFilterer, AzSubObject, AzSubObjectContainer):
    @classmethod
    def azobject_name_list(cls):
        return ['image', 'gallery']

    @classmethod
    def get_parent_class(cls):
        from .resourcegroup import ResourceGroup
        return ResourceGroup

    @classmethod
    def get_child_classes(cls):
        from .imagedefinition import ImageDefinition
        return [ImageDefinition]

    @classmethod
    def get_cmd_base(cls):
        return ['sig']

    @classmethod
    def get_self_id_argconfig_dest(cls, is_parent):
        return 'gallery_name'

    @classmethod
    def get_create_action_argconfigs(cls):
        return [NoWaitBoolArgConfig()]

    @classmethod
    def get_delete_action_argconfigs(cls):
        return [NoWaitBoolArgConfig()]
