
from .azobject import AzSubObject
from .azobject import AzSubObjectContainer
from .storageblob import StorageBlob


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
        return {'--auth-mode': 'login'}

    @classmethod
    def get_azsubobject_cmd_args(cls, parent, cmdname, opts):
        # Unfortunately storage container cmds (and subcmds) do *not* accept the resource group arg :(
        return {k: v for k, v in super().get_azsubobject_cmd_args(parent, cmdname, opts).items()
                if k not in ['-g', '--resource-group']}

    @classmethod
    def get_azsubobject_classes(cls):
        return [StorageBlob]
