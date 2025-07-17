
from ..exception import NotCreatable
from ..exception import NotDeletable
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
    def get_base_cmd(cls):
        return ['account']

    @classmethod
    def get_create_cmd(cls):
        raise NotCreatable('subscription')

    @classmethod
    def get_delete_cmd(cls):
        raise NotDeletable('subscription')

    def get_my_subcmd_opts(self, **kwargs):
        return ['--subscription', self.object_id]
