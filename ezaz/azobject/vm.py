
from . import AzSubObject


class VM(AzSubObject):
    @classmethod
    def subobject_name_list(cls):
        return ['vm']

    def get_my_cmd_args(self, opts):
        return {'--name': self.object_id}

    def get_my_subcmd_args(self, opts):
        return {}

    def get_my_create_args(self, opts):
        args = {'--accept-term': None,
                '--enable-secure-boot': None,
                '--enable-vtpm': None,
                '--image': self.required_arg('image', 'create', opts)}
        return self.get_my_cmd_args(opts) | args
