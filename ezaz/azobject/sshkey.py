
from .azobject import AzSubObject


class SshKey(AzSubObject):
    @classmethod
    def azobject_name_list(cls):
        return ['sshkey']

    @classmethod
    def azobject_arg(cls):
        return '--ssh-public-key-name'

    def _get_my_create_cmd_args(self, opts):
        return self.required_args_one(['ssh-key', 'ssh-key-file'], 'create', opts)
