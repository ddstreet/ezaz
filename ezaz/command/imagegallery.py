
from .command import AzObjectActionCommand


class ImageGalleryCommand(AzObjectActionCommand):
    @classmethod
    def azclass(cls):
        from ..azobject.imagegallery import ImageGallery
        return ImageGallery

    @classmethod
    def aliases(cls):
        return ['sig']
