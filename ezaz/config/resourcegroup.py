
from contextlib import suppress

from ..exception import ImageGalleryConfigNotFound
from ..exception import SshKeyConfigNotFound
from ..exception import StorageAccountConfigNotFound
from ..exception import VMConfigNotFound
from .imagegallery import ImageGalleryConfig
from .sshkey import SshKeyConfig
from .storageaccount import StorageAccountConfig
from .vm import VMConfig


class ResourceGroupConfig:
    @classmethod
    def _CURRENT_IMAGE_GALLERY_KEY(cls):
        return 'current_image_gallery'

    @classmethod
    def _IMAGE_GALLERY_KEY(cls, image_gallery):
        return f'image_gallery:{image_gallery}'

    @classmethod
    def _CURRENT_SSH_KEY_KEY(cls):
        return 'current_ssh_key'

    @classmethod
    def _SSH_KEY_KEY(cls, ssh_key):
        return f'ssh_key:{ssh_key}'

    @classmethod
    def _CURRENT_STORAGE_ACCOUNT_KEY(cls):
        return 'current_storage_account'

    @classmethod
    def _STORAGE_ACCOUNT_KEY(cls, storage_account):
        return f'storage_account:{storage_account}'

    @classmethod
    def _CURRENT_VM_KEY(cls):
        return 'current_vm'

    @classmethod
    def _VM_KEY(cls, vm):
        return f'vm:{vm}'

    def __init__(self, parent, config):
        self._parent = parent
        self._config = config

    def _save(self):
        self._parent._save()

    @property
    def current_image_gallery(self):
        with suppress(KeyError):
            return self._config[self._CURRENT_IMAGE_GALLERY_KEY()]
        raise ImageGalleryConfigNotFound

    @current_image_gallery.setter
    def current_image_gallery(self, image_gallery):
        if not image_gallery:
            del self.current_image_gallery
        else:
            self._config[self._CURRENT_IMAGE_GALLERY_KEY()] = image_gallery
            self._save()

    @current_image_gallery.deleter
    def current_image_gallery(self):
        with suppress(KeyError):
            del self._config[self._CURRENT_IMAGE_GALLERY_KEY()]
            self._save()

    def get_image_gallery(self, image_gallery):
        k = self._IMAGE_GALLERY_KEY(image_gallery)
        return ImageGalleryConfig(self, self._config.setdefault(k, {}))

    def del_image_gallery(self, image_gallery):
        k = self._IMAGE_GALLERY_KEY(image_gallery)
        with suppress(KeyError):
            del self._config[k]
            self._save()

    @property
    def current_ssh_key(self):
        with suppress(KeyError):
            return self._config[self._CURRENT_SSH_KEY_KEY()]
        raise SshKeyConfigNotFound

    @current_ssh_key.setter
    def current_ssh_key(self, ssh_key):
        if not ssh_key:
            del self.current_ssh_key
        else:
            self._config[self._CURRENT_SSH_KEY_KEY()] = ssh_key
            self._save()

    @current_ssh_key.deleter
    def current_ssh_key(self):
        with suppress(KeyError):
            del self._config[self._CURRENT_SSH_KEY_KEY()]
            self._save()

    def get_ssh_key(self, ssh_key):
        k = self._SSH_KEY_KEY(ssh_key)
        return SshKeyConfig(self, self._config.setdefault(k, {}))

    def del_ssh_key(self, ssh_key):
        k = self._SSH_KEY_KEY(ssh_key)
        with suppress(KeyError):
            del self._config[k]
            self._save()

    @property
    def current_storage_account(self):
        with suppress(KeyError):
            return self._config[self._CURRENT_STORAGE_ACCOUNT_KEY()]
        raise StorageAccountConfigNotFound

    @current_storage_account.setter
    def current_storage_account(self, storage_account):
        if not storage_account:
            del self.current_storage_account
        else:
            self._config[self._CURRENT_STORAGE_ACCOUNT_KEY()] = storage_account
            self._save()

    @current_storage_account.deleter
    def current_storage_account(self):
        with suppress(KeyError):
            del self._config[self._CURRENT_STORAGE_ACCOUNT_KEY()]
            self._save()

    def get_storage_account(self, storage_account):
        k = self._STORAGE_ACCOUNT_KEY(storage_account)
        return StorageAccountConfig(self, self._config.setdefault(k, {}))

    def del_storage_account(self, storage_account):
        k = self._STORAGE_ACCOUNT_KEY(storage_account)
        with suppress(KeyError):
            del self._config[k]
            self._save()

    @property
    def current_vm(self):
        with suppress(KeyError):
            return self._config[self._CURRENT_VM_KEY()]
        raise VMConfigNotFound

    @current_vm.setter
    def current_vm(self, vm):
        if not vm:
            del self.current_vm
        else:
            self._config[self._CURRENT_VM_KEY()] = vm
            self._save()

    @current_vm.deleter
    def current_vm(self):
        with suppress(KeyError):
            del self._config[self._CURRENT_VM_KEY()]
            self._save()

    def get_vm(self, vm):
        k = self._VM_KEY(vm)
        return VMConfig(self, self._config.setdefault(k, {}))

    def del_vm(self, vm):
        k = self._VM_KEY(vm)
        with suppress(KeyError):
            del self._config[k]
            self._save()
