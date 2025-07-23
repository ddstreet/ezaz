
from pathlib import Path

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
                                  help='Public key file (required for --create, defaults to public key in ~/.ssh)')

    def create(self):
        if not self._options.public_key:
            self._options.public_key = self._read_public_key_file(self._options.public_key_file)
        super().create()

    def _read_public_key_file(self, public_key_file):
        f = public_key_file or self._find_public_key_file()
        if not f:
            return None
        keyfile = Path(f).expanduser()
        if not Path(keyfile).is_file():
            print(f'Public key file does not exist: {keyfile}')
            return None
        keytext = keyfile.read_text().strip()
        if 'PRIVATE KEY' in keytext:
            print(f'Private key found in {keyfile}')
            if keyfile.suffix.lower() != '.pub':
                pubkeyfile = keyfile.with_suffix('.pub')
                print(f'Trying corresponding public key file {pubkeyfile}')
                return self._read_public_key_file(pubkeyfile)
        return keytext

    def _find_public_key_file(self):
        for keytype in ['ed25519', 'rsa']:
            keypath = Path(f'~/.ssh/id_{keytype}.pub').expanduser()
            if keypath.is_file():
                if self.verbose:
                    print(f'Using ssh public key {keypath}')
                return str(keypath)
        if self.verbose:
            print('No ssh public key found')
        return None
