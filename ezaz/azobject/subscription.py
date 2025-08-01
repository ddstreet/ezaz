
from .azobject import AzSubObjectContainer
from .azobject import AzListable
from .azobject import AzShowable
from .location import Location
from .resourcegroup import ResourceGroup


class Subscription(AzShowable, AzListable, AzSubObjectContainer):
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
    def get_cmd_base(cls):
        return ['account']
