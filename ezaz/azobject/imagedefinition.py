
from . import AzSubObject
from . import AzSubObjectContainer


class ImageDefinition(AzSubObject, AzSubObjectContainer()):
    @classmethod
    def subobject_name_list(cls):
        return ['image', 'definition']

    @classmethod
    def show_cmd(cls):
        return ['sig', 'image-definition', 'show']

    @classmethod
    def list_cmd(cls):
        return ['sig', 'image-definition', 'list']

    def cmd_opts(self):
        return self.subcmd_opts()

    def subcmd_opts(self):
        return super().subcmd_opts() + ['--gallery-image-definition', self.object_id]
