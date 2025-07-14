
from ..exception import VMConfigNotFound
from . import AzObjectTemplate


class VM(AzObjectTemplate()):
    @classmethod
    def _cls_type(cls):
        return 'vm'

    @classmethod   
    def _cls_config_not_found(cls):
        return VMConfigNotFound

    @classmethod
    def _cls_show_info_cmd(cls):
        return ['vm', 'show']

    @classmethod
    def _cls_list_info_cmd(cls):
        return ['vm', 'list']

    def _info_opts(self):
        return super()._subcommand_info_opts() + ['--name', self.object_id]

    def _subcommand_info_opts(self):
        return super()._subcommand_info_opts() + ['--FIXME-name', self.object_id]
