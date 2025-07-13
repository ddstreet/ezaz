
from contextlib import suppress

from ..exception import ImageDefinitionConfigNotFound
from .subconfig import SubConfig
from .imagedefinition import ImageDefinitionConfig


class ImageGalleryConfig(SubConfig):
    @classmethod
    def _DEFAULT_IMAGE_DEFINITION_KEY(cls):
        return 'default_image_definition'

    @classmethod
    def _IMAGE_DEFINITION_KEY(cls, image_definition):
        return f'image_definition:{image_definition}'

    @property
    def default_image_definition(self):
        with suppress(KeyError):
            return self._config[self._DEFAULT_IMAGE_DEFINITION_KEY()]
        raise ImageDefinitionConfigNotFound

    @default_image_definition.setter
    def default_image_definition(self, image_definition):
        if not image_definition:
            del self.default_image_definition
        else:
            self._config[self._DEFAULT_IMAGE_DEFINITION_KEY()] = image_definition
            self._save()

    @default_image_definition.deleter
    def default_image_definition(self):
        with suppress(KeyError):
            del self._config[self._DEFAULT_IMAGE_DEFINITION_KEY()]
            self._save()

    def get_image_definition(self, image_definition):
        k = self._IMAGE_DEFINITION_KEY(image_definition)
        return ImageDefinitionConfig(self._config.setdefault(k, {}))

    def del_image_definition(self, image_definition):
        k = self._IMAGE_DEFINITION_KEY(image_definition)
        with suppress(KeyError):
            del self._config[k]
            self._save()

    def get_default_image_definition(self):
        return self.get_image_definition(self.default_image_definition)
