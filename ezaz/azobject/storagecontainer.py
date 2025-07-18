
from contextlib import suppress

from . import AzSubObject
from . import AzSubObjectContainer


class StorageContainer(AzSubObject, AzSubObjectContainer([])):
    @classmethod
    def subobject_name_list(cls):
        return ['storage', 'container']

    @classmethod
    def filter_parent_args(cls, *args):
        # Unfortunately storage container cmds do *not* accept the resource group arg :(
        for arg in ['-g', '--resource-group']:
            with suppress(ValueError):
                index = args.index(arg)
                args = args[0:index] + args[index+2:]
        return list(args) + ['--auth-mode', 'login']

    def get_parent_subcmd_args(self, **kwargs):
        return self.filter_parent_args(super().get_parent_subcmd_args(**kwargs))

    def get_my_cmd_args(self, **kwargs):
        return ['--name', self.object_id]

    def get_my_subcmd_args(self, **kwargs):
        return ['--container-name', self.object_id]
