
from . import AzObject


class ImageDefinition(AzObject):
    def __init__(self, name, image_gallery, info=None):
        if info:
            assert info.name == name
        self._name = name
        self._image_gallery = image_gallery
        self._image_definition_info = info

    @property
    def subscription_id(self):
        return self._image_gallery.subscription_id

    @property
    def resource_group_name(self):
        return self._image_gallery.resource_group_name

    @property
    def image_gallery_name(self):
        return self._image_gallery.name

    @property
    def name(self):
        return self._name

    @property
    def config(self):
        return self._image_gallery.config.get_image_definition(self.name)

    @property
    def image_definition_info(self):
        if not self._image_definition_info:
            self._image_definition_info = self.az_response('sig', 'image-definition', 'show',
                                                            '--subscription', self.subscription_id,
                                                            '-g', self.resource_group_name,
                                                            '-r', self.image_gallery_name,
                                                            '-n', self.name)
        return self._image_definition_info
