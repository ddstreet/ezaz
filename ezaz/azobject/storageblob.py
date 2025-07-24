
from .azobject import AzSubObject


class StorageBlob(AzSubObject):
    @classmethod
    def azobject_name_list(cls):
        return ['storage', 'blob']

    @classmethod
    def azobject_cmd_arg(cls):
        return '--name'

    @classmethod
    def XX_get_azsubobject_cmd_args(self, parent, cmdname, opts):
        return {'--auth-mode': 'login'}

    @classmethod
    def XXget_azsubobject_cmd_args(cls, parent, cmdname, opts):
        # Unfortunately storage container cmds do *not* accept the resource group arg :(
        args = super().get_azsubobject_cmd_args(parent, cmdname, opts)
        args.pop('-g', None)
        args.pop('--resource-group', None)
        return args
