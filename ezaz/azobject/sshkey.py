
from contextlib import suppress
from pathlib import Path

from ..argutil import ArgMap
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
    def get_base_cmd(cls):
        return ['sshkey']

    @classmethod
    def azobject_cmd_arg(cls):
        return '--ssh-public-key-name'

    def _get_cmd_args(self, cmdname, opts):
        if cmdname == 'create':
            args = self._public_key_arg(opts)
            return ArgMap(args, self._public_key_type_arg(args.get('--public-key')))
        if cmdname == 'delete':
            return self.optional_flag_arg('yes', opts)
        return super()._get_cmd_args(cmdname, opts)

    def _public_key_type_arg(self, keytext):
        if keytext.startswith('ssh-ed25519'):
            return self._opts_to_args(encryption_type='Ed25519')
        elif keytext.startswith('ssh-rsa'):
            return self._opts_to_args(encryption_type='RSA')
        else:
            raise ArgumentError(f'Invalid ssh public key: {keytext}')

    def _public_key_arg(self, opts, required_by='create'):
        with suppress(RequiredArgument):
            return self.required_arg('public_key', opts, required_by)
        with suppress(FileNotFoundError):
            public_key_file = opts.get('public_key_file', None)
            return self._opts_to_args(public_key=self._public_key_text(public_key_file))
        raise RequiredArgumentGroup(['public_key', 'public_key_file'], required_by)

    def _public_key_text(self, public_key_file):
        keyfile = self._public_key_path(public_key_file)
        keytext = keyfile.read_text().strip()
        if 'PRIVATE KEY' in keytext:
            if self.verbose:
                print(f'Private key found in {keyfile}')
            if keyfile.suffix.lower() != '.pub':
                pubkeyfile = keyfile.with_suffix('.pub')
                if self.verbose:
                    print(f'Trying corresponding public key file {pubkeyfile}')
                return self._public_key_text(str(pubkeyfile))
        return keytext

    def _public_key_path(self, public_key_file):
        for k in (([public_key_file] if public_key_file else []) +
                  [self._pubkey(keytype) for keytype in ['ed25519', 'rsa']]):
            keypath = Path(k).expanduser().resolve()
            if keypath.is_file():
                if self.verbose:
                    print(f'Using ssh public key {keypath}')
                return keypath
        raise FileNotFoundError()

    def _pubkey(self, keytype):
        return f'~/.ssh/id_{keytype}.pub'
