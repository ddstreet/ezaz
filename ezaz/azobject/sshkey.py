
from contextlib import suppress
from pathlib import Path

from ..argutil import ArgConfig
from ..argutil import ArgMap
from ..argutil import FileArgConfig
from ..argutil import GroupArgConfig
from ..argutil import YesFlagArgConfig
from ..exception import ArgumentError
from ..exception import RequiredArgument
from ..exception import RequiredArgumentGroup
from .azobject import AzCommonActionable
from .azobject import AzSubObject


class SshKey(AzCommonActionable, AzSubObject):
    @classmethod
    def azobject_name_list(cls):
        return ['ssh', 'key']

    @classmethod
    def get_cmd_base(cls):
        return ['sshkey']

    @classmethod
    def get_parent_class(cls):
        from .resourcegroup import ResourceGroup
        return ResourceGroup

    @classmethod
    def get_self_id_argconfig_cmddest(cls, is_parent):
        return 'ssh_public_key_name'

    @classmethod
    def get_create_action_argconfigs(cls):
        return [GroupArgConfig(ArgConfig('public_key',
                                         help='Public key data'),
                               FileArgConfig('public_key_file',
                                             default=cls.find_public_key_file,
                                             help='Public key file'),
                               cmddest='public_key',
                               required=True)]

    @classmethod
    def get_delete_action_argconfigs(cls):
        return [YesFlagArgConfig()]

    @classmethod
    def find_public_key_file(cls, **opts):
        for keytype in ['ed25519', 'rsa']:
            keyfile = Path(f'~/.ssh/id_{keytype}.pub').expanduser().resolve()
            if keyfile.is_file():
                return str(keyfile)
        return None
