
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
    def parser_add_common_arguments(cls, parser):
        super().parser_add_common_arguments(parser)
        parser.add_argument('--os-type', choices=['linux', 'windows'], default='linux', help="OS type (default: 'linux')")
        parser.add_argument('--offer', help='Offer (required for --create)')
        parser.add_argument('--publisher', help='Publisher (required for --create)')
        parser.add_argument('--sku', help='SKU (required for --create)')
