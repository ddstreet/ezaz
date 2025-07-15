
from contextlib import suppress

from . import AzSubObject
from . import AzSubObjectContainer


class StorageContainer(AzSubObject, AzSubObjectContainer([])):
    @classmethod
    def subobject_name_list(cls):
        return ['storage', 'container']

    @classmethod
    def show_cmd(cls):
        return ['storage', 'container', 'show']

    @classmethod
    def list_cmd(cls):
        return ['storage', 'container', 'list']

    def _subcmd_opts_without_rg(self):
        # Unfortunately storage container cmds do *not* include the resource group :(
        opts = super().subcmd_opts()
        for opt in ['-g', '--resource-group']:
            with suppress(ValueError):
                index = opts.index(opt)
                opts = opts[0:index] + opts[index+2:]
        return opts

    def cmd_opts(self):
        return self._subcmd_opts_without_rg() + ['--auth-mode', 'login', '--name', self.object_id]

    def subcmd_opts(self):
        return self._subcmd_opts_without_rg() + ['--auth-mode', 'login', '--container-name', self.object_id]
