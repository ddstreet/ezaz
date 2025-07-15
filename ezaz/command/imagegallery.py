
from .command import DefineSubCommand
from .resourcegroup import ResourceGroupSubCommand


class ImageGalleryCommand(ResourceGroupSubCommand):
    @classmethod
    def command_name_list(cls):
        return ['image', 'gallery']

    @classmethod
    def aliases(cls):
        return ['sig']

    def _show(self, image_gallery):
        info = image_gallery.info
        msg = info.name
        if self.verbose:
            msg += f' (location: {info.location})'
        print(msg)


ImageGallerySubCommand = DefineSubCommand(ResourceGroupSubCommand, ImageGalleryCommand)
