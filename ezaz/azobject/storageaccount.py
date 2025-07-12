
from . import AzObject
from .storagecontainer import StorageContainer


class StorageAccount(AzObject):
    def __init__(self, name, resource_group, info=None):
        if info:
            assert info.name == name
        self._name = name
        self._resource_group = resource_group
        self._storage_account_info = info

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
        return self._subscription.config.get_storage_account(self.name)

    @property
    def storage_account_info(self):
        if not self._storage_account_info:
            self._storage_account_info = self.az_response('storage', 'account', 'show',
                                                          '--subscription', self.subscription_id,
                                                          '-g', self.resource_group_name,
                                                          '-n', self.name)
        return self._storage_account_info

    @property
    def current_storage_container(self):
        return self.config.current_storage_container

    @current_storage_container.setter
    def current_storage_container(self, storage_container):
        if self.current_storage_container != storage_container:
            self.config.current_storage_container = storage_container

    def get_storage_container(self, storage_container, info=None):
        return StorageContainer(storage_container, self, info=info)

    def get_current_storage_container(self):
        return self.get_storage_container(self.current_storage_container)

    def get_storage_containers(self):
        return [self.get_storage_container(info.name, info=info)
                for info in self.az_responselist('storage', 'container', 'list',
                                                 '--subscription', self.subscription_id,
                                                 '--auth-mode', 'login',
                                                 '--account-name', self.name)]
