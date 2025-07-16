
from .command import AllActionCommand
from .resourcegroup import ResourceGroupCommand


class ImageGalleryCommand(AllActionCommand):
    @classmethod
    def parent_command_cls(cls):
        return ResourceGroupCommand

    @classmethod
    def command_name_list(cls):
        return ['image', 'gallery']

    @classmethod
    def aliases(cls):
        return ['sig']
