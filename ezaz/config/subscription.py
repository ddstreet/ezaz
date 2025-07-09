
from contextlib import suppress

from ..exception import ResourceGroupConfigNotFound
from .resourcegroup import ResourceGroupConfig


class SubscriptionConfig:
    @classmethod
    def _CURRENT_RESOURCE_GROUP_KEY(cls):
        return 'current_resource_group'

    @classmethod
    def _RESOURCE_GROUP_KEY(cls, resource_group):
        return f'resource_group:{resource_group}'

    def __init__(self, parent, config):
        self._parent = parent
        self._config = config

    def _save(self):
        self._parent._save()

    @property
    def current_resource_group(self):
        with suppress(KeyError):
            return self._config[self._CURRENT_RESOURCE_GROUP_KEY()]
        raise ResourceGroupConfigNotFound

    @current_resource_group.setter
    def current_resource_group(self, resource_group):
        if not resource_group:
            del self.current_resource_group
        else:
            self._config[self._CURRENT_RESOURCE_GROUP_KEY()] = resource_group
            self._save()

    @current_resource_group.deleter
    def current_resource_group(self):
        with suppress(KeyError):
            del self._config[self._CURRENT_RESOURCE_GROUP_KEY()]
            self._save()

    def get_resource_group(self, resource_group):
        k = self._RESOURCE_GROUP_KEY(resource_group)
        return ResourceGroupConfig(self, self._config.setdefault(k, {}))

    def del_resource_group(self, resource_group):
        k = self._RESOURCE_GROUP_KEY(resource_group)
        with suppress(KeyError):
            del self._config[k]
            self._save()
