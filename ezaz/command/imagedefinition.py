
from .command import ImageGallerySubCommand


class ImageDefinitionCommand(ImageGallerySubCommand):
    @classmethod
    def _cls_type_list(cls):
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

