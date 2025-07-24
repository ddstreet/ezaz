
from ..exception import ArgumentError
from .azobject import AzSubObject


class SshKey(AzSubObject):
    @classmethod
    def azobject_name_list(cls):
        return ['ssh', 'key']

    @classmethod
    def get_base_cmd(cls):
        return ['sshkey']

    @classmethod
    def azobject_cmd_arg(cls):
        return '--ssh-public-key-name'

    def _get_cmd_args(self, cmdname, opts):
        if cmdname == 'create':
            args = self.required_arg('public_key', opts, 'create')
            v = args[self._name_to_arg('public_key')]
            if v.startswith('ssh-ed25519'):
                args[self._name_to_arg('encryption_type')] = 'Ed25519'
            elif v.startswith('ssh-rsa'):
                args[self._name_to_arg('encryption_type')] = 'RSA'
            elif v.startswith('ecdsa'):
                args[self._name_to_arg('encryption_type')] = 'ECDSA'
            else:
                raise ArgumentError(f'Invalid ssh public key: {v}')
            return args
        return {}
