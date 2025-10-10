
from .command import AzObjectActionCommand


class LocationCommand(AzObjectActionCommand):
    @classmethod
    def azclass(cls):
        from ..azobject.location import Location
        return Location

    @classmethod
    def has_portal_url(cls):
        return False
