
from ..exception import ImageGalleryConfigNotFound
from . import AzObjectTemplate
from .imagedefinition import ImageDefinition


class ImageGallery(AzObjectTemplate([ImageDefinition])):
    @classmethod
    def _cls_type(cls):
        return 'image_gallery'

    @classmethod
    def _cls_config_not_found(cls):
        return ImageGalleryConfigNotFound

    @classmethod
    def _cls_show_info_cmd(cls):
        return ['sig', 'show']

    @classmethod
    def _cls_list_info_cmd(cls):
        return ['sig', 'list']

    def _info_opts(self):
        return self._subcommand_info_opts()

    def _subcommand_info_opts(self):
        return super()._subcommand_info_opts() + ['--gallery-name', self.object_id]
