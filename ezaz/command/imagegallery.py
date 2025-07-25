
from ..azobject.imagegallery import ImageGallery
from .command import AllActionCommand
from .resourcegroup import ResourceGroupCommand


class ImageGalleryCommand(AllActionCommand):
    @classmethod
    def parent_command_cls(cls):
        return ResourceGroupCommand

    @classmethod
    def azobject_class(cls):
        return ImageGallery

    @classmethod
    def aliases(cls):
        return ['sig']
