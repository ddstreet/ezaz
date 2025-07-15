
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
    def show_cmd(cls):
        return ['account', 'show']

    @classmethod
    def list_cmd(cls):
        return ['account', 'list']

    def cmd_opts(self):
        return super().subcmd_opts() + ['--subscription', self.object_id]

    def subcmd_opts(self):
        return super().subcmd_opts() + ['--subscription', self.object_id]
