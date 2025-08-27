
from .command import AzCommonActionCommand


class ImageGalleryCommand(AzCommonActionCommand):
    @classmethod
    def azclass(cls):
        from ..azobject.imagegallery import ImageGallery
        return ImageGallery

    @classmethod
    def aliases(cls):
        return ['sig']
