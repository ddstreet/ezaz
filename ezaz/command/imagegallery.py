
from .command import AzCommonActionCommand


class ImageGalleryCommand(AzCommonActionCommand):
    @classmethod
    def parent_command_cls(cls):
        from .resourcegroup import ResourceGroupCommand
        return ResourceGroupCommand

    @classmethod
    def azclass(cls):
        from ..azobject.imagegallery import ImageGallery
        return ImageGallery

    @classmethod
    def aliases(cls):
        return ['sig']
