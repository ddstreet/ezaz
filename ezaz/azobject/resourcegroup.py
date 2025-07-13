
from ..exception import ResourceGroupConfigNotFound
from . import StandardAzObjectTemplate
from .imagegallery import ImageGallery
from .sshkey import SshKey
from .storageaccount import StorageAccount
from .vm import VM


class ResourceGroup(StandardAzObjectTemplate([ImageGallery, SshKey, StorageAccount, VM])):
    @classmethod
    def _cls_type(cls):
        return 'resource_group'

    @classmethod
    def _cls_config_not_found(cls):
        return ResourceGroupConfigNotFound

    @classmethod
    def _cls_show_info_cmd(cls):
        return ['group', 'show']

    @classmethod
    def _cls_list_info_cmd(cls):
        return ['group', 'list']

    def _info_opts(self):
        return self._subcommand_info_opts()

    def _subcommand_info_opts(self):
        return super()._subcommand_info_opts() + ['--resource-group', self.object_id]
