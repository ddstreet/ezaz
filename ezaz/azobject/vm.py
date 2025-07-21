
from .azobject import AzSubObject


class VM(AzSubObject):
    @classmethod
    def subobject_name_list(cls):
        return ['vm']

    def get_my_cmd_args(self, opts):
        return {'--name': self.object_id}

    def get_my_subcmd_args(self, opts):
        return {}

    def _get_my_create_args(self, opts):
        args = {'--accept-term': None,
                '--enable-secure-boot': None,
                '--enable-vtpm': None}
        return self._merge_cmd_args(self.required_arg('image', opts, 'create'), args)
