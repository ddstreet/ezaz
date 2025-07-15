
from . import AzSubObject


class VM(AzSubObject):
    @classmethod
    def subobject_name_list(cls):
        return ['vm']

    @classmethod
    def show_cmd(cls):
        return ['vm', 'show']

    @classmethod
    def list_cmd(cls):
        return ['vm', 'list']

    def cmd_opts(self):
        return super().subcmd_opts() + ['--name', self.object_id]

    def subcmd_opts(self):
        return super().subcmd_opts() + ['--FIXME-name', self.object_id]
