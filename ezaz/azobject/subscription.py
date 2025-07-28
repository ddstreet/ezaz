
from ..exception import NotCreatable
from ..exception import NotDeletable
from .azobject import AzSubObject
from .azobject import AzSubObjectContainer
from .location import Location
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
        return [ResourceGroup, Location]

    @classmethod
    def get_base_cmd(cls):
        return ['account']

    @classmethod
    def _get_cmd(cls, cmdname):
        if cmdname == 'create':
            raise NotCreatable('subscription')
        if cmdname == 'delete':
            raise NotDeletable('subscription')
        return super()._get_cmd(cmdname)

    def show(self):
        print(self.info if self.verbose else f'{self.info.name} ({self.info.id})')
