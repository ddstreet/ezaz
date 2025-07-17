
from . import AzSubObject


class VM(AzSubObject):
    @classmethod
    def subobject_name_list(cls):
        return ['vm']

    def get_my_cmd_opts(self, **kwargs):
        return ['--name', self.object_id]
