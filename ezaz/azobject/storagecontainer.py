
from contextlib import suppress

from . import AzSubObject
from . import AzSubObjectContainer


class StorageContainer(AzSubObject, AzSubObjectContainer([])):
    @classmethod
    def subobject_name_list(cls):
        return ['storage', 'container']

    @classmethod
    def get_show_cmd(cls):
        return ['storage', 'container', 'show']

    @classmethod
    def get_create_cmd(self):
        raise NotCreatable()

    @classmethod
    def get_delete_cmd(self):
        raise NotDeletable()

    @classmethod
    def get_list_cmd(cls):
        return ['storage', 'container', 'list']

    @classmethod
    def filter_parent_opts(cls, *opts):
        # Unfortunately storage container cmds do *not* include the resource group :(
        for opt in ['-g', '--resource-group']:
            with suppress(ValueError):
                index = opts.index(opt)
                opts = opts[0:index] + opts[index+2:]
        return list(opts) + ['--auth-mode', 'login']

    def get_cmd_opts(self):
        return self.filter_parent_opts(super().get_subcmd_opts()) + ['--name', self.object_id]

    def get_subcmd_opts(self):
        return self.filter_parent_opts(super().get_subcmd_opts()) + ['--container-name', self.object_id]
