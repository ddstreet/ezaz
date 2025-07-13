
from .command import ResourceGroupSubCommand
from .command import StandardActionCommand


class ImageGalleryCommand(StandardActionCommand, ResourceGroupSubCommand):
    @classmethod
    def name(cls):
        return 'imagegallery'

    @classmethod
    def _action_target_name(cls):
        return 'image gallery'

    @classmethod
    def _action_target_attr(self):
        return 'image_gallery'

    @classmethod
    def aliases(cls):
        return ['sig']

    def _show(self, image_gallery):
        info = image_gallery.image_gallery_info
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

