
from .command import ImageGallerySubCommand
from .command import StandardActionCommand


class ImageDefinitionCommand(ImageGallerySubCommand, StandardActionCommand):
    ACTION_ARGUMENT_NAME = 'image definition'
    ACTION_ARGUMENT_METAVAR = 'DEFINITION'
    ACTION_ATTR_NAME = 'image_definition'

    @classmethod
    def name(cls):
        return 'imagedefinition'

    def _show(self, image_definition):
        info = image_definition.image_definition_info
        msg = info.name
        if self.verbose:
            msg += f' (location: {info.location})'
            if info.tags:
                tags = []
                for k in info.tags:
                    v = getattr(info.tags, k)
                    tags.append(k if not v else f'{k}={v}')
                msg += f' [tags: {" ".join(tags)}]'
        print(msg)

