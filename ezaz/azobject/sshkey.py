
from .azobject import AzSubObject


class SshKey(AzSubObject):
    @classmethod
    def subobject_name_list(cls):
        return ['sshkey']

    def get_my_cmd_args(self, opts):
        return {'--ssh-public-key-name': self.object_id}

    def get_my_create_cmd_args(self, opts):
        return self.get_my_cmd_args(opts) | self.required_args_one(['ssh-key', 'ssh-key-file'], 'create', opts)
