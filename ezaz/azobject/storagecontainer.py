
from contextlib import suppress

from .azobject import AzCommonActionable
from .azobject import AzSubObject
from .azobject import AzSubObjectContainer
from .storageblob import StorageBlob
from .storagekey import StorageKey


class StorageContainer(AzCommonActionable, AzSubObject, AzSubObjectContainer):
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
    def get_azsubobject_classes(cls):
        return [StorageBlob]

    @classmethod
    def get_subcmd_args_from_parent(cls, parent, cmdname, opts):
        args = super().get_subcmd_args_from_parent(parent, cmdname, opts)
        return {k: v for k, v in args.items() if k not in ['-g', '--resource-group']}

    @classmethod
    def get_parent_storage_account_key(self, parent):
        keys = parent.get_azsubobjects(StorageKey.azobject_name())
        with suppress(IndexError):
            return keys[0].key_value
        return None

    @classmethod
    def get_action_configmap(cls):
        return {}

    @property
    def storage_account_key(self):
        return self.get_parent_storage_account_key(self.parent)

    def get_action_cmd_args(self, action, opts):
        return ArgMap(super().get_action_cmd_args(action, opts),
                      self._args_to_opts(account_key=self.storage_account_key,
                                         auth_mode='key'))
