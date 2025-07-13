
from contextlib import suppress

from ..exception import StorageContainerConfigNotFound
from .subconfig import SubConfig
from .storagecontainer import StorageContainerConfig


class StorageAccountConfig(SubConfig):
    @classmethod
    def _DEFAULT_STORAGE_CONTAINER_KEY(cls):
        return 'default_storage_container'

    @classmethod
    def _STORAGE_CONTAINER_KEY(cls, storage_container):
        return f'storage_container:{storage_container}'

    @property
    def default_storage_container(self):
        with suppress(KeyError):
            return self._config[self._DEFAULT_STORAGE_CONTAINER_KEY()]
        raise StorageContainerConfigNotFound

    @default_storage_container.setter
    def default_storage_container(self, storage_container):
        if not storage_container:
            del self.default_storage_container
        else:
            self._config[self._DEFAULT_STORAGE_CONTAINER_KEY()] = storage_container
            self._save()

    @default_storage_container.deleter
    def default_storage_container(self):
        with suppress(KeyError):
            del self._config[self._DEFAULT_STORAGE_CONTAINER_KEY()]
            self._save()

    def get_storage_container(self, storage_container):
        k = self._STORAGE_CONTAINER_KEY(storage_container)
        return StorageContainerConfig(self, self._config.setdefault(k, {}))

    def del_storage_container(self, storage_container):
        k = self._STORAGE_CONTAINER_KEY(storage_container)
        with suppress(KeyError):
            del self._config[k]
            self._save()

    def get_default_storage_container(self):
        return self.get_storage_container(self.default_storage_container)
