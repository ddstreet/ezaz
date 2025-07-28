
from contextlib import suppress

from .azobject import AzSubObject
from .azobject import AzSubObjectContainer
from .storageblob import StorageBlob
from .storagekey import StorageKey


class StorageContainer(AzSubObject, AzSubObjectContainer):
    @classmethod
    def azobject_name_list(cls):
        return ['storage', 'container']

    @classmethod
    def azobject_cmd_arg(cls):
        return '--name'

    @classmethod
    def azobject_subcmd_arg(cls):
        return '--container-name'

    @classmethod
    def _get_azsubobject_cmd_args(self, parent, cmdname, opts):
        return {'--auth-mode': 'key'}

    @classmethod
    def get_azsubobject_cmd_args(cls, parent, cmdname, opts):
        # Unfortunately storage container cmds (and subcmds) do *not* accept the resource group arg :(
        return {k: v for k, v in super().get_azsubobject_cmd_args(parent, cmdname, opts).items()
                if k not in ['-g', '--resource-group']}

    @classmethod
    def get_azsubobject_classes(cls):
        return [StorageBlob]

    def _get_cmd_args(self, cmdname, opts):
        if cmdname == 'create':
            key = self.storage_account_key or self.required_arg('account_key', opts, 'create')
            return {'--account-key': key}
        return super()._get_cmd_args(cmdname, opts)

    @property
    def storage_account_key(self):
        keys = self.parent.get_azsubobjects(StorageKey.azobject_name())
        with suppress(IndexError):
            return keys[0].key_value
        return None
