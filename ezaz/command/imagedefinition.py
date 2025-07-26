
from ..azobject.imagedefinition import ImageDefinition
from .command import AllActionCommand
from .imagegallery import ImageGalleryCommand


class ImageDefinitionCommand(AllActionCommand):
    @classmethod
    def parent_command_cls(cls):
        return ImageGalleryCommand

    @classmethod
    def azobject_class(cls):
        return ImageDefinition

    @classmethod
    def parser_add_create_action_arguments(cls, parser):
        parser.add_argument('--os-type',
                            choices=['linux', 'windows'],
                            default='linux',
                            help="OS type (default: 'linux')")
        parser.add_argument('--offer',
                            required=True,
                            help='Offer')
        parser.add_argument('--publisher',
                            required=True,
                            help='Publisher')
        parser.add_argument('--sku',
                            required=True,
                            help='SKU')
