
from ..azobject.imagedefinition import ImageDefinition
from .command import AzSubObjectActionCommand
from .imagegallery import ImageGalleryCommand


class ImageDefinitionCommand(AzSubObjectActionCommand):
    @classmethod
    def parent_command_cls(cls):
        return ImageGalleryCommand

    @classmethod
    def azclass(cls):
        return ImageDefinition
