
from .command import AzCommonActionCommand


class LocationCommand(AzCommonActionCommand):
    @classmethod
    def azclass(cls):
        from ..azobject.location import Location
        return Location
