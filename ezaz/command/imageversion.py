
from .command import AzSubObjectActionCommand


class ImageVersionCommand(AzSubObjectActionCommand):
    @classmethod
    def parent_command_cls(cls):
        from .imagedefinition import ImageDefinitionCommand
        return ImageDefinitionCommand

    @classmethod
    def azclass(cls):
        from ..azobject.imageversion import ImageVersion
        return ImageVersion
