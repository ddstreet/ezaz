
from . import AzSubObject


class SshKey(AzSubObject):
    @classmethod
    def subobject_name_list(cls):
        return ['ssh', 'key']

    @classmethod
    def get_show_cmd(cls):
        return ['sshkey', 'show']

    @classmethod
    def get_create_cmd(self):
        raise NotCreatable()

    @classmethod
    def get_delete_cmd(self):
        raise NotDeletable()

    @classmethod
    def get_list_cmd(cls):
        return ['sshkey', 'list']

    def get_cmd_opts(self):
        return self.get_subcmd_opts()

    def get_subcmd_opts(self):
        return super().get_subcmd_opts() + ['--ssh-public-key-name', self.object_id]
