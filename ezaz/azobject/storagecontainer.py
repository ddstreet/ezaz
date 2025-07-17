
from contextlib import suppress

from . import AzSubObject
from . import AzSubObjectContainer


class StorageContainer(AzSubObject, AzSubObjectContainer([])):
    @classmethod
    def subobject_name_list(cls):
        return ['storage', 'container']

    @classmethod
    def filter_parent_opts(cls, *opts):
        # Unfortunately storage container cmds do *not* include the resource group :(
        for opt in ['-g', '--resource-group']:
            with suppress(ValueError):
                index = opts.index(opt)
                opts = opts[0:index] + opts[index+2:]
        return list(opts) + ['--auth-mode', 'login']

    def get_parent_subcmd_opts(self, **kwargs):
        return self.filter_parent_opts(super().get_parent_subcmd_opts(**kwargs))

    def get_my_cmd_opts(self, **kwargs):
        return ['--name', self.object_id]

    def get_my_subcmd_opts(self, **kwargs):
        return ['--container-name', self.object_id]
