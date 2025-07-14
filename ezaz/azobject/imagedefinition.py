
from ..exception import ImageDefinitionConfigNotFound
from . import AzObjectTemplate


class ImageDefinition(AzObjectTemplate()):
    @classmethod
    def _cls_type(cls):
        return 'image_definition'

    @classmethod
    def _cls_config_not_found(cls):
        return ImageDefinitionConfigNotFound

    @classmethod
    def _cls_show_info_cmd(cls):
        return ['sig', 'image-definition', 'show']

    @classmethod
    def _cls_list_info_cmd(cls):
        return ['sig', 'image-definition', 'list']

    def _info_opts(self):
        return self._subcommand_info_opts()

    def _subcommand_info_opts(self):
        return super()._subcommand_info_opts() + ['--gallery-image-definition', self.object_id]
