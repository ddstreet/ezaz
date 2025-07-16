
from .command import AllActionCommand
from .imagegallery import ImageGalleryCommand


class ImageDefinitionCommand(AllActionCommand):
    @classmethod
    def parent_command_cls(cls):
        return ImageGalleryCommand

    @classmethod
    def command_name_list(cls):
        return ['image', 'definition']
