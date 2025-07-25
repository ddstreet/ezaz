
from .command import AzSubObjectActionCommand


class ImageDefinitionCommand(AzSubObjectActionCommand):
    @classmethod
    def parent_command_cls(cls):
        from .imagegallery import ImageGalleryCommand
        return ImageGalleryCommand

    @classmethod
    def azclass(cls):
        from ..azobject.imagedefinition import ImageDefinition
        return ImageDefinition
