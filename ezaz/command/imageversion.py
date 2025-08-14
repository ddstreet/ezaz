
from ..azobject.imageversion import ImageVersion
from .command import AzSubObjectActionCommand
from .imagedefinition import ImageDefinitionCommand


class ImageVersionCommand(AzSubObjectActionCommand):
    @classmethod
    def parent_command_cls(cls):
        return ImageDefinitionCommand

    @classmethod
    def azclass(cls):
        return ImageVersion
