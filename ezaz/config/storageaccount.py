
from contextlib import suppress

from ..exception import StorageContainerConfigNotFound
from .storagecontainer import StorageContainerConfig


class StorageAccountConfig:
    @classmethod
    def _CURRENT_STORAGE_CONTAINER_KEY(cls):
        return 'current_storage_container'

    @classmethod
    def _STORAGE_CONTAINER_KEY(cls, storage_container):
        return f'storage_container:{storage_container}'

    def __init__(self, parent, config):
        self._parent = parent
        self._config = config

    def _save(self):
        self._parent._save()

    @property
    def current_storage_container(self):
        with suppress(KeyError):
            return self._config[self._CURRENT_STORAGE_CONTAINER_KEY()]
        raise StorageContainerConfigNotFound

    @current_storage_container.setter
    def current_storage_container(self, storage_container):
        if not storage_container:
            del self.current_storage_container
        else:
            self._config[self._CURRENT_STORAGE_CONTAINER_KEY()] = storage_container
            self._save()

    @current_storage_container.deleter
    def current_storage_container(self):
        with suppress(KeyError):
            del self._config[self._CURRENT_STORAGE_CONTAINER_KEY()]
            self._save()

    def get_storage_container(self, storage_container):
        k = self._STORAGE_CONTAINER_KEY(storage_container)
        return StorageContainerConfig(self, self._config.setdefault(k, {}))

    def del_storage_container(self, storage_container):
        k = self._STORAGE_CONTAINER_KEY(storage_container)
        with suppress(KeyError):
            del self._config[k]
            self._save()
