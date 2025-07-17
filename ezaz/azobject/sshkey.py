
from . import AzSubObject


class SshKey(AzSubObject):
    @classmethod
    def subobject_name_list(cls):
        return ['ssh', 'key']

    @classmethod
    def get_base_cmd(cls):
        return ['sshkey']

    def get_subcmd_opts(self, **kwargs):
        return ['--ssh-public-key-name', self.object_id]
