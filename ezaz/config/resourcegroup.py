
from contextlib import suppress

from ..exception import ImageGalleryConfigNotFound
from ..exception import SshKeyConfigNotFound
from ..exception import StorageAccountConfigNotFound
from ..exception import VMConfigNotFound
from .subconfig import SubConfig
from .imagegallery import ImageGalleryConfig
from .sshkey import SshKeyConfig
from .storageaccount import StorageAccountConfig
from .vm import VMConfig


class ResourceGroupConfig(SubConfig):
    @classmethod
    def _DEFAULT_IMAGE_GALLERY_KEY(cls):
        return 'default_image_gallery'

    @classmethod
    def _IMAGE_GALLERY_KEY(cls, image_gallery):
        return f'image_gallery:{image_gallery}'

    @classmethod
    def _DEFAULT_SSH_KEY_KEY(cls):
        return 'default_ssh_key'

    @classmethod
    def _SSH_KEY_KEY(cls, ssh_key):
        return f'ssh_key:{ssh_key}'

    @classmethod
    def _DEFAULT_STORAGE_ACCOUNT_KEY(cls):
        return 'default_storage_account'

    @classmethod
    def _STORAGE_ACCOUNT_KEY(cls, storage_account):
        return f'storage_account:{storage_account}'

    @classmethod
    def _DEFAULT_VM_KEY(cls):
        return 'default_vm'

    @classmethod
    def _VM_KEY(cls, vm):
        return f'vm:{vm}'

    @property
    def default_image_gallery(self):
        with suppress(KeyError):
            return self._config[self._DEFAULT_IMAGE_GALLERY_KEY()]
        raise ImageGalleryConfigNotFound

    @default_image_gallery.setter
    def default_image_gallery(self, image_gallery):
        if not image_gallery:
            del self.default_image_gallery
        else:
            self._config[self._DEFAULT_IMAGE_GALLERY_KEY()] = image_gallery
            self._save()

    @default_image_gallery.deleter
    def default_image_gallery(self):
        with suppress(KeyError):
            del self._config[self._DEFAULT_IMAGE_GALLERY_KEY()]
            self._save()

    def get_image_gallery(self, image_gallery):
        k = self._IMAGE_GALLERY_KEY(image_gallery)
        return ImageGalleryConfig(self, self._config.setdefault(k, {}))

    def del_image_gallery(self, image_gallery):
        k = self._IMAGE_GALLERY_KEY(image_gallery)
        with suppress(KeyError):
            del self._config[k]
            self._save()

    def get_default_image_gallery(self):
        return self.get_image_gallery(self.default_image_gallery)

    @property
    def default_ssh_key(self):
        with suppress(KeyError):
            return self._config[self._DEFAULT_SSH_KEY_KEY()]
        raise SshKeyConfigNotFound

    @default_ssh_key.setter
    def default_ssh_key(self, ssh_key):
        if not ssh_key:
            del self.default_ssh_key
        else:
            self._config[self._DEFAULT_SSH_KEY_KEY()] = ssh_key
            self._save()

    @default_ssh_key.deleter
    def default_ssh_key(self):
        with suppress(KeyError):
            del self._config[self._DEFAULT_SSH_KEY_KEY()]
            self._save()

    def get_ssh_key(self, ssh_key):
        k = self._SSH_KEY_KEY(ssh_key)
        return SshKeyConfig(self, self._config.setdefault(k, {}))

    def del_ssh_key(self, ssh_key):
        k = self._SSH_KEY_KEY(ssh_key)
        with suppress(KeyError):
            del self._config[k]
            self._save()

    def get_default_ssh_key(self):
        return self.get_ssh_key(self.default_ssh_key)

    @property
    def default_storage_account(self):
        with suppress(KeyError):
            return self._config[self._DEFAULT_STORAGE_ACCOUNT_KEY()]
        raise StorageAccountConfigNotFound

    @default_storage_account.setter
    def default_storage_account(self, storage_account):
        if not storage_account:
            del self.default_storage_account
        else:
            self._config[self._DEFAULT_STORAGE_ACCOUNT_KEY()] = storage_account
            self._save()

    @default_storage_account.deleter
    def default_storage_account(self):
        with suppress(KeyError):
            del self._config[self._DEFAULT_STORAGE_ACCOUNT_KEY()]
            self._save()

    def get_storage_account(self, storage_account):
        k = self._STORAGE_ACCOUNT_KEY(storage_account)
        return StorageAccountConfig(self, self._config.setdefault(k, {}))

    def del_storage_account(self, storage_account):
        k = self._STORAGE_ACCOUNT_KEY(storage_account)
        with suppress(KeyError):
            del self._config[k]
            self._save()

    def get_default_storage_account(self):
        return self.get_storage_account(self.default_storage_account)

    @property
    def default_vm(self):
        with suppress(KeyError):
            return self._config[self._DEFAULT_VM_KEY()]
        raise VMConfigNotFound

    @default_vm.setter
    def default_vm(self, vm):
        if not vm:
            del self.default_vm
        else:
            self._config[self._DEFAULT_VM_KEY()] = vm
            self._save()

    @default_vm.deleter
    def default_vm(self):
        with suppress(KeyError):
            del self._config[self._DEFAULT_VM_KEY()]
            self._save()

    def get_vm(self, vm):
        k = self._VM_KEY(vm)
        return VMConfig(self, self._config.setdefault(k, {}))

    def del_vm(self, vm):
        k = self._VM_KEY(vm)
        with suppress(KeyError):
            del self._config[k]
            self._save()

    def get_default_vm(self):
        return self.get_vm(self.default_vm)
