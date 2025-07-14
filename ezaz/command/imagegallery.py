
from .command import ResourceGroupSubCommand
from .command import StandardActionCommand


class ImageGalleryCommand(ResourceGroupSubCommand, StandardActionCommand):
    ACTION_ARGUMENT_NAME = 'image gallery'
    ACTION_ARGUMENT_METAVAR = 'GALLERY'
    ACTION_ATTR_NAME = 'image_gallery'

    @classmethod
    def name(cls):
        return 'imagegallery'

    @classmethod
    def aliases(cls):
        return ['sig']

    def _show(self, image_gallery):
        info = image_gallery.info
        msg = info.name
        if self.verbose:
            msg += f' (location: {info.location})'
        print(msg)

