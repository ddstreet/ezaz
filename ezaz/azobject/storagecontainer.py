
from contextlib import suppress

from .azobject import AzSubObject


class StorageContainer(AzSubObject):
    @classmethod
    def azobject_name_list(cls):
        return ['storage', 'container']

    @classmethod
    def azobject_arg(cls):
        return '--name'

    @classmethod
    def filter_parent_args(cls, args):
        # Unfortunately storage container cmds do *not* accept the resource group arg :(
        args.pop('-g', None)
        args.pop('--resource-group', None)
        return args

    def get_parent_subcmd_args(self, opts):
        return self.filter_parent_args(super().get_parent_subcmd_args(opts))

    def get_my_subcmd_args(self, opts):
        return {'--container-name': self.object_id,
                '--auth-mode': 'login'}
