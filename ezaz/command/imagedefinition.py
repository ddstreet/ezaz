
from .command import SubCommand
from .imagegallery import ImageGalleryCommand


class ImageDefinitionCommand(SubCommand):
    @classmethod
    def parent_command_cls(cls):
        return ImageGalleryCommand

    @classmethod
    def command_name_list(cls):
        return ['image', 'definition']

    def _show(self, image_definition):
        info = image_definition.info
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
