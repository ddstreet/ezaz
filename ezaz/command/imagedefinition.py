
from ..azobject.imagedefinition import ImageDefinition
from .command import CommonActionCommand
from .imagegallery import ImageGalleryCommand


class ImageDefinitionCommand(CommonActionCommand):
    @classmethod
    def parent_command_cls(cls):
        return ImageGalleryCommand

    @classmethod
    def azclass(cls):
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
        parser.add_argument('--architecture',
                            choices=['Arm64', 'x64'],
                            default='x64',
                            help='CPU architecture')

    @classmethod
    def parser_add_delete_action_arguments(cls, parser):
        parser.add_argument('--no-wait',
                            action='store_true',
                            help='Do not wait for long-running operation to finish')
