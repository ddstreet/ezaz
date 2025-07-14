
from ..exception import SubscriptionConfigNotFound
from . import AzObjectTemplate
from .resourcegroup import ResourceGroup


class Subscription(AzObjectTemplate([ResourceGroup])):
    @classmethod
    def _cls_type(cls):
        return 'subscription'

    @classmethod
    def _cls_info_id(cls, info):
        return info.id

    @classmethod
    def _cls_config_not_found(cls):
        return SubscriptionConfigNotFound

    @classmethod
    def _cls_show_info_cmd(cls):
        return ['account', 'show']

    @classmethod
    def _cls_list_info_cmd(cls):
        return ['account', 'list']

    def _info_opts(self):
        return self._subcommand_info_opts()

    def _subcommand_info_opts(self):
        return super()._subcommand_info_opts() + ['--subscription', self.object_id]
