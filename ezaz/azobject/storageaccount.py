
from ..exception import StorageAccountConfigNotFound
from . import StandardAzObjectTemplate
from .storagecontainer import StorageContainer


class StorageAccount(StandardAzObjectTemplate([StorageContainer])):
    @classmethod
    def _cls_type(cls):
        return 'storage_account'

    @classmethod
    def _cls_config_not_found(cls):
        return StorageAccountConfigNotFound

    @classmethod
    def _cls_show_info_cmd(cls):
        return ['storage', 'account', 'show']

    @classmethod
    def _cls_list_info_cmd(cls):
        return ['storage', 'account', 'list']

    def _info_opts(self):
        return super()._subcommand_info_opts() + ['--name', self.object_id]

    def _subcommand_info_opts(self):
        return super()._subcommand_info_opts() + ['--account-name', self.object_id]
