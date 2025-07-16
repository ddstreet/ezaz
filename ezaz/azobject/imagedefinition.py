
from . import AzSubObject
from . import AzSubObjectContainer


class ImageDefinition(AzSubObject, AzSubObjectContainer()):
    @classmethod
    def subobject_name_list(cls):
        return ['image', 'definition']

    @classmethod
    def get_show_cmd(cls):
        return ['sig', 'image-definition', 'show']

    @classmethod
    def get_create_cmd(self):
        raise NotCreatable()

    @classmethod
    def get_delete_cmd(self):
        raise NotDeletable()

    @classmethod
    def get_list_cmd(cls):
        return ['sig', 'image-definition', 'list']

    def get_cmd_opts(self):
        return self.get_subcmd_opts()

    def get_subcmd_opts(self):
        return super().get_subcmd_opts() + ['--gallery-image-definition', self.object_id]
