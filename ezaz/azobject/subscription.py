
from .azobject import AzSubObject
from .azobject import AzSubObjectContainer
from .azobject import AzListable
from .location import Location
from .resourcegroup import ResourceGroup


class Subscription(AzListable, AzSubObject, AzSubObjectContainer):
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

    def show(self):
        print(self.info if self.verbose else f'{self.info.name} ({self.info.id})')
