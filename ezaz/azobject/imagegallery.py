
from . import AzObject


class ImageGallery(AzObject):
    def __init__(self, name, resource_group, info=None):
        if info:
            assert info.name == name
        self._name = name
        self._resource_group = resource_group
        self._image_gallery_info = info

    @property
    def subscription_id(self):
        return self._resource_group.subscription_id

    @property
    def resource_group_name(self):
        return self._resource_group.name

    @property
    def name(self):
        return self._name

    @property
    def config(self):
        return self._subscription.config.get_image_gallery(self.name)

    @property
    def image_gallery_info(self):
        if not self._image_gallery_info:
            self._image_gallery_info = self.az_response('sig', 'show',
                                                        '--subscription', self.subscription_id,
                                                        '-g', self.resource_group_name,
                                                        '-n', self.name)
        return self._image_gallery_info

    @property
    def current_image_definition(self):
        return self.config.current_image_definition

    @current_image_definition.setter
    def current_image_definition(self, image_definition):
        if self.current_image_definition != image_definition:
            self.config.current_image_definition = image_definition

    def get_image_definition(self, image_definition, info=None):
        return ImageDefinition(image_definition, self, info=info)

    def get_current_image_definition(self):
        return self.get_image_definition(self.current_image_definition)

    def get_image_definitions(self):
        return [self.get_image_definition(info.name, info=info)
                for info in self.az_responselist('sig', 'image-definition', 'list',
                                                 '--subscription', self.subscription_id,
                                                 '-g', self.resource_group_name,
                                                 '-r', self.name)]
