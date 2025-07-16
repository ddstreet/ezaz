
from . import AzSubObject
from . import AzSubObjectContainer
from .imagedefinition import ImageDefinition


class ImageGallery(AzSubObject, AzSubObjectContainer([ImageDefinition])):
    @classmethod
    def subobject_name_list(cls):
        return ['image', 'gallery']

    @classmethod
    def get_show_cmd(cls):
        return ['sig', 'show']

    @classmethod
    def get_create_cmd(self):
        raise NotCreatable()

    @classmethod
    def get_delete_cmd(self):
        raise NotDeletable()

    @classmethod
    def get_list_cmd(cls):
        return ['sig', 'list']

    def get_cmd_opts(self):
        return self.get_subcmd_opts()

    def get_subcmd_opts(self):
        return super().get_subcmd_opts() + ['--gallery-name', self.object_id]
