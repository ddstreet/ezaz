
from ..azobject.imagegallery import ImageGallery
from .command import AzSubObjectActionCommand
from .resourcegroup import ResourceGroupCommand


class ImageGalleryCommand(AzSubObjectActionCommand):
    @classmethod
    def parent_command_cls(cls):
        return ResourceGroupCommand

    @classmethod
    def azclass(cls):
        return ImageGallery

    @classmethod
    def aliases(cls):
        return ['sig']
