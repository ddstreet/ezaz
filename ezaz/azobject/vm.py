
from . import AzSubObject


class VM(AzSubObject):
    @classmethod
    def subobject_name_list(cls):
        return ['vm']

    @classmethod
    def get_show_cmd(cls):
        return ['vm', 'show']

    @classmethod
    def get_create_cmd(self):
        raise NotCreatable()

    @classmethod
    def get_delete_cmd(self):
        raise NotDeletable()

    @classmethod
    def get_list_cmd(cls):
        return ['vm', 'list']

    def get_cmd_opts(self):
        return super().get_subcmd_opts() + ['--name', self.object_id]

    def get_subcmd_opts(self):
        return super().get_subcmd_opts() + ['--FIXME-name', self.object_id]
