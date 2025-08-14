
from ..argutil import NoWaitBoolArgConfig
from .azobject import AzCommonActionable
from .azobject import AzSubObject


class ImageVersion(AzCommonActionable, AzSubObject):
    @classmethod
    def azobject_name_list(cls):
        return ['image', 'version']

    @classmethod
    def get_cmd_base(cls):
        return ['sig', 'image-version']

    @classmethod
    def get_parent_class(cls):
        from .imagedefinition import ImageDefinition
        return ImageDefinition

    @classmethod
    def get_self_id_argconfig_dest(cls, is_parent):
        return 'gallery_image_version'

    @classmethod
    def get_create_action_argconfigs(cls):
        return []

    @classmethod
    def get_delete_action_argconfigs(cls):
        return [NoWaitBoolArgConfig()]
