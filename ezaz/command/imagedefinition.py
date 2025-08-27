
from .command import AzCommonActionCommand


class ImageDefinitionCommand(AzCommonActionCommand):
    @classmethod
    def parent_command_cls(cls):
        from .imagegallery import ImageGalleryCommand
        return ImageGalleryCommand

    @classmethod
    def azclass(cls):
        from ..azobject.imagedefinition import ImageDefinition
        return ImageDefinition
