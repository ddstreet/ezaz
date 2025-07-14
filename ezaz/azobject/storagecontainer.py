
from contextlib import suppress

from ..exception import StorageContainerConfigNotFound
from . import AzObjectTemplate


class StorageContainer(AzObjectTemplate([])):
    @classmethod
    def _cls_type(cls):
        return 'storage_container'

    @classmethod
    def _cls_config_not_found(cls):
        return StorageContainerConfigNotFound

    @classmethod
    def _cls_show_info_cmd(cls):
        return ['storage', 'container', 'show']

    @classmethod
    def _cls_list_info_cmd(cls):
        return ['storage', 'container', 'list']

    def _parent_info_opts(self):
        # Unfortunately storage container cmds do *not* include the resource group :(
        opts = super()._subcommand_info_opts()
        for opt in ['-g', '--resource-group']:
            with suppress(ValueError):
                index = opts.index(opt)
                opts = opts[0:index] + opts[index+2:]
        return opts

    def _info_opts(self):
        return self._parent_info_opts() + ['--auth-mode', 'login', '--name', self.object_id]

    def _subcommand_info_opts(self):
        return self._parent_info_opts() + ['--auth-mode', 'login', '--container-name', self.object_id]
