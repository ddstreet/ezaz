
from . import AzSubObject


class SshKey(AzSubObject):
    @classmethod
    def subobject_name_list(cls):
        return ['ssh', 'key']

    @classmethod
    def show_cmd(cls):
        return ['sshkey', 'show']

    @classmethod
    def list_cmd(cls):
        return ['sshkey', 'list']

    def cmd_opts(self):
        return self.subcmd_opts()

    def subcmd_opts(self):
        return super().subcmd_opts() + ['--ssh-public-key-name', self.object_id]
