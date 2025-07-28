
from contextlib import suppress
from pathlib import Path

from ..exception import ArgumentError
from ..exception import RequiredArgument
from ..exception import RequiredArgumentGroup
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
            args = self._get_public_key_arg(opts)
            v = args[self._name_to_arg('public_key')]
            if v.startswith('ssh-ed25519'):
                args |= self._kwargs_to_args(encryption_type='Ed25519')
            elif v.startswith('ssh-rsa'):
                args |= self._kwargs_to_args(encryption_type='RSA')
            else:
                raise ArgumentError(f'Invalid ssh public key: {v}')
            return args
        return {}

    def _get_public_key_arg(self, opts, required_by='create'):
        with suppress(RequiredArgument):
            return self.required_arg('public_key', opts, required_by)
        keytext = self._read_public_key_file(opts.get('public_key_file', None))
        if not keytext:
            raise RequiredArgumentGroup(['public_key', 'public_key_file'], required_by)
        return self._kwargs_to_args(public_key=keytext)

    def _read_public_key_file(self, public_key_file):
        f = public_key_file or self._find_public_key_file()
        if not f:
            return None
        keyfile = Path(f).expanduser()
        if not Path(keyfile).is_file():
            if self.verbose:
                print(f'Public key file does not exist: {keyfile}')
            return None
        keytext = keyfile.read_text().strip()
        if 'PRIVATE KEY' in keytext:
            if self.verbose:
                print(f'Private key found in {keyfile}')
            if keyfile.suffix.lower() != '.pub':
                pubkeyfile = keyfile.with_suffix('.pub')
                if self.verbose:
                    print(f'Trying corresponding public key file {pubkeyfile}')
                return self._read_public_key_file(pubkeyfile)
        return keytext

    def _find_public_key_file(self):
        for keytype in ['ed25519', 'rsa']:
            keypath = Path(f'~/.ssh/id_{keytype}.pub').expanduser().resolve()
            if keypath.is_file():
                if self.verbose:
                    print(f'Using ssh public key {keypath}')
                return str(keypath)
        if self.verbose:
            print('No ssh public key found')
        return None
