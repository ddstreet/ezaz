
from . import AzSubObject
from . import AzSubObjectContainer
from .resourcegroup import ResourceGroup


class Subscription(AzSubObject, AzSubObjectContainer([ResourceGroup])):
    @classmethod
    def subobject_name_list(cls):
        return ['subscription']

    @classmethod
    def info_id(cls, info):
        return info.id

    @classmethod
    def get_show_cmd(cls):
        return ['account', 'show']

    @classmethod
    def get_list_cmd(cls):
        return ['account', 'list']

    def get_cmd_opts(self):
        return super().get_subcmd_opts() + ['--subscription', self.object_id]

    def get_subcmd_opts(self):
        return super().get_subcmd_opts() + ['--subscription', self.object_id]
