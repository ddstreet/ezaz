
from .command import AzObjectActionCommand


class ImageDefinitionCommand(AzObjectActionCommand):
    @classmethod
    def azclass(cls):
        from ..azobject.imagedefinition import ImageDefinition
        return ImageDefinition
