
from contextlib import suppress

from ..exception import StorageBlobConfigNotFound
from .storageblob import StorageBlobConfig


class StorageContainerConfig:
    @classmethod
    def _CURRENT_STORAGE_BLOB_KEY(cls):
        return 'current_storage_blob'

    @classmethod
    def _STORAGE_BLOB_KEY(cls, storage_blob):
        return f'storage_blob:{storage_blob}'

    def __init__(self, parent, config):
        self._parent = parent
        self._config = config

    def _save(self):
        self._parent._save()

    @property
    def current_storage_blob(self):
        with suppress(KeyError):
            return self._config[self._CURRENT_STORAGE_BLOB_KEY()]
        raise StorageBlobConfigNotFound

    @current_storage_blob.setter
    def current_storage_blob(self, storage_blob):
        if not storage_blob:
            del self.current_storage_blob
        else:
            self._config[self._CURRENT_STORAGE_BLOB_KEY()] = storage_blob
            self._save()

    @current_storage_blob.deleter
    def current_storage_blob(self):
        with suppress(KeyError):
            del self._config[self._CURRENT_STORAGE_BLOB_KEY()]
            self._save()

    def get_storage_blob(self, storage_blob):
        k = self._STORAGE_BLOB_KEY(storage_blob)
        return StorageBlobConfig(self, self._config.setdefault(k, {}))

    def del_storage_blob(self, storage_blob):
        k = self._STORAGE_BLOB_KEY(storage_blob)
        with suppress(KeyError):
            del self._config[k]
            self._save()
