
from ..exception import SshKeyConfigNotFound
from . import AzObjectTemplate


class SshKey(AzObjectTemplate()):
    @classmethod
    def _cls_type(cls):
        return 'ssh_key'

    @classmethod   
    def _cls_config_not_found(cls):
        return SshKeyConfigNotFound

    @classmethod
    def _cls_show_info_cmd(cls):
        return ['sshkey', 'show']

    @classmethod
    def _cls_list_info_cmd(cls):
        return ['sshkey', 'list']

    def _info_opts(self):
        return self._subcommand_info_opts()

    def _subcommand_info_opts(self):
        return super()._subcommand_info_opts() + ['--ssh-public-key-name', self.object_id]
