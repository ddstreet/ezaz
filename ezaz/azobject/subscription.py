
from ..exception import NotCreatable
from ..exception import NotDeletable
from .azobject import AzSubObject
from .azobject import AzSubObjectContainer
from .resourcegroup import ResourceGroup


class Subscription(AzSubObject, AzSubObjectContainer):
    @classmethod
    def azobject_name_list(cls):
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

    def show_current(self):
        print(self.parent.get_current_subscription_id())

    def set_current(self, **kwargs):
        self.parent.set_current_subscription_id(self.required_arg_value('subscription', kwargs, 'set_current'))
