
from .command import AzCommonActionCommand


class ImageDefinitionCommand(AzCommonActionCommand):
    @classmethod
    def azclass(cls):
        from ..azobject.imagedefinition import ImageDefinition
        return ImageDefinition
