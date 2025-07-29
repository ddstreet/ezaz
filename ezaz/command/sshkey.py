
from pathlib import Path

from ..azobject.sshkey import SshKey
from .command import CommonActionCommand
from .resourcegroup import ResourceGroupCommand


class SshKeyCommand(CommonActionCommand):
    @classmethod
    def parent_command_cls(cls):
        return ResourceGroupCommand

    @classmethod
    def azobject_class(cls):
        return SshKey

    @classmethod
    def parser_add_create_action_arguments(cls, parser):
        pubkey_group = parser.add_mutually_exclusive_group()
        pubkey_group.add_argument('--public-key',
                                  help='Public key data')
        pubkey_group.add_argument('--public-key-file',
                                  help='Public key file (defaults to public key in ~/.ssh)')

    @classmethod
    def parser_add_delete_action_arguments(cls, parser):
        parser.add_argument('-y', '--yes',
                            action='store_true',
                            help='Do not prompt for confirmation')
