
from . import AzSubObject
from . import AzSubObjectContainer
from .imagedefinition import ImageDefinition


class ImageGallery(AzSubObject, AzSubObjectContainer([ImageDefinition])):
    @classmethod
    def subobject_name_list(cls):
        return ['image', 'gallery']

    @classmethod
    def show_cmd(cls):
        return ['sig', 'show']

    @classmethod
    def list_cmd(cls):
        return ['sig', 'list']

    def cmd_opts(self):
        return self.subcmd_opts()

    def subcmd_opts(self):
        return super().subcmd_opts() + ['--gallery-name', self.object_id]
