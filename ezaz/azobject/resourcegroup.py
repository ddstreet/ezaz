
from . import AzObject
from .imagegallery import ImageGallery
from .sshkey import SshKey
from .storageaccount import StorageAccount
from .vm import VM


class ResourceGroup(AzObject):
    def __init__(self, name, subscription, info=None):
        if info:
            assert info.name == name
        self._name = name
        self._subscription = subscription
        self._resource_group_info = info

    @property
    def subscription_id(self):
        return self._subscription.subscription_id

    @property
    def name(self):
        return self._name

    @property
    def config(self):
        return self._subscription.config.get_resource_group(self.name)

    @property
    def resource_group_info(self):
        if not self._resource_group_info:
            self._resource_group_info = self.az_response('group', 'show',
                                                       '--subscription', self.subscription_id,
                                                       '-g', self.name)
        return self._resource_group_info

    @property
    def current_image_gallery(self):
        return self.config.current_image_gallery

    @current_image_gallery.setter
    def current_image_gallery(self, image_gallery):
        if self.current_image_gallery != image_gallery:
            self.config.current_image_gallery = image_gallery

    def get_image_gallery(self, image_gallery, info=None):
        return ImageGallery(image_gallery, self, info=info)

    def get_current_image_gallery(self):
        return self.get_image_gallery(self.current_image_gallery)

    def get_image_gallerys(self):
        return [self.get_image_gallery(info.name, info=info)
                for info in self.az_responselist('sig', 'list',
                                                 '--subscription', self.subscription_id,
                                                 '-g', self.name)]

    # For proper spelling
    def get_image_galleries(self):
        return get_image_gallerys()

    @property
    def current_ssh_key(self):
        return self.config.current_ssh_key

    @current_ssh_key.setter
    def current_ssh_key(self, ssh_key):
        if self.current_ssh_key != ssh_key:
            self.config.current_ssh_key = ssh_key

    def get_ssh_key(self, ssh_key, info=None):
        return SshKey(ssh_key, self, info=info)

    def get_current_ssh_key(self):
        return self.get_ssh_key(self.current_ssh_key)

    def get_ssh_keys(self):
        return [self.get_ssh_key(info.name, info=info)
                for info in self.az_responselist('sshkey', 'list',
                                                 '--subscription', self.subscription_id,
                                                 '-g', self.name)]

    @property
    def current_storage_account(self):
        return self.config.current_storage_account

    @current_storage_account.setter
    def current_storage_account(self, storage_account):
        if self.current_storage_account != storage_account:
            self.config.current_storage_account = storage_account

    def get_storage_account(self, storage_account, info=None):
        return StorageAccount(storage_account, self, info=info)

    def get_current_storage_account(self):
        return self.get_storage_account(self.current_storage_account)

    def get_storage_accounts(self):
        return [self.get_storage_account(info.name, info=info)
                for info in self.az_responselist('storage', 'account', 'list',
                                                 '--subscription', self.subscription_id,
                                                 '-g', self.name)]

    @property
    def current_vm(self):
        return self.config.current_vm

    @current_vm.setter
    def current_vm(self, vm):
        if self.current_vm != vm:
            self.config.current_vm = vm

    def get_vm(self, vm, info=None):
        return VM(vm, self, info=info)

    def get_current_vm(self):
        return self.get_vm(self.current_vm)

    def get_vms(self):
        return [self.get_vm(info.name, info=info)
                for info in self.az_responselist('vm', 'list',
                                                 '--subscription', self.subscription_id,
                                                 '-g', self.name)]
