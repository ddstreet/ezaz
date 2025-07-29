
from ..azobject.imagegallery import ImageGallery
from .command import CommonActionCommand
from .resourcegroup import ResourceGroupCommand


class ImageGalleryCommand(CommonActionCommand):
    @classmethod
    def parent_command_cls(cls):
        return ResourceGroupCommand

    @classmethod
    def azobject_class(cls):
        return ImageGallery

    @classmethod
    def aliases(cls):
        return ['sig']

    @classmethod
    def parser_add_create_action_arguments(cls, parser):
        parser.add_argument('--no-wait',
                            action='store_true',
                            help='Do not wait for long-running operation to finish')

    @classmethod
    def parser_add_delete_action_arguments(cls, parser):
        parser.add_argument('--no-wait',
                            action='store_true',
                            help='Do not wait for long-running operation to finish')
