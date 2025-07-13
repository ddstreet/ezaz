
from contextlib import suppress

from ..exception import ResourceGroupConfigNotFound
from .subconfig import SubConfig
from .resourcegroup import ResourceGroupConfig


class SubscriptionConfig(SubConfig):
    @classmethod
    def _DEFAULT_RESOURCE_GROUP_KEY(cls):
        return 'default_resource_group'

    @classmethod
    def _RESOURCE_GROUP_KEY(cls, resource_group):
        return f'resource_group:{resource_group}'

    @property
    def default_resource_group(self):
        with suppress(KeyError):
            return self._config[self._DEFAULT_RESOURCE_GROUP_KEY()]
        raise ResourceGroupConfigNotFound

    @default_resource_group.setter
    def default_resource_group(self, resource_group):
        if not resource_group:
            del self.default_resource_group
        else:
            self._config[self._DEFAULT_RESOURCE_GROUP_KEY()] = resource_group
            self._save()

    @default_resource_group.deleter
    def default_resource_group(self):
        with suppress(KeyError):
            del self._config[self._DEFAULT_RESOURCE_GROUP_KEY()]
            self._save()

    def get_resource_group(self, resource_group):
        k = self._RESOURCE_GROUP_KEY(resource_group)
        return ResourceGroupConfig(self, self._config.setdefault(k, {}))

    def del_resource_group(self, resource_group):
        k = self._RESOURCE_GROUP_KEY(resource_group)
        with suppress(KeyError):
            del self._config[k]
            self._save()

    def get_default_resource_group(self):
        return self.get_resource_group(self.default_resource_group)
