
from . import AzSubObject


class VM(AzSubObject):
    @classmethod
    def subobject_name_list(cls):
        return ['vm']

    def get_my_cmd_opts(self, **kwargs):
        return ['--name', self.object_id]

    def get_my_subcmd_opts(self, **kwargs):
        return []

    def get_my_create_opts(self, **kwargs):
        image = self.required_arg_by_arg('image', 'create', **kwargs)
        opts = ['--accept-term',
                '--enable-secure-boot',
                '--enable-vtpm',
                '--image', image]
        return super().get_my_create_opts(**kwargs) + opts
