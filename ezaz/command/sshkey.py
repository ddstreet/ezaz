
from .command import AllActionCommand
from .resourcegroup import ResourceGroupCommand


COMMANDS = ['SshKeyCommand']


class SshKeyCommand(AllActionCommand):
    @classmethod
    def parent_command_cls(cls):
        return ResourceGroupCommand

    @classmethod
    def command_name_list(cls):
        return ['sshkey']

    @classmethod
    def parser_add_common_arguments(cls, parser):
        super().parser_add_common_arguments(parser)
        pubkey_group = parser.add_mutually_exclusive_group()
        pubkey_group.add_argument('--public-key',
                                  help='Public key data (required for --create)')
        pubkey_group.add_argument('--public-key-file',
                                  help='Public key file (required for --create)')
