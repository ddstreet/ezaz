
from ..exception import NotCreatable
from ..exception import NotDeletable
from .azobject import AzSubObject
from .azobject import AzSubObjectContainer
from .resourcegroup import ResourceGroup


class Subscription(AzSubObject, AzSubObjectContainer):
    @classmethod
    def subobject_name_list(cls):
        return ['subscription']

    @classmethod
    def info_id(cls, info):
        return info.id

    @classmethod
    def get_azsubobject_classes(cls):
        return [ResourceGroup]

    @classmethod
    def get_base_cmd(cls):
        return ['account']

    @classmethod
    def get_create_cmd(cls):
        raise NotCreatable('subscription')

    @classmethod
    def get_delete_cmd(cls):
        raise NotDeletable('subscription')

    def get_my_cmd_args(self, opts):
        return {'--subscription': self.object_id}
