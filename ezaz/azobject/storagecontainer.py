
from . import AzObject


class StorageContainer(AzObject):
    def __init__(self, name, storage_account, info=None):
        if info:
            assert info.name == name
        self._name = name
        self._storage_account = storage_account
        self._storage_container_info = info

    @property
    def subscription_id(self):
        return self._storage_account.subscription_id

    @property
    def resource_group_name(self):
        return self._storage_account.resource_group_name

    @property
    def storage_account_name(self):
        return self._storage_account.name

    @property
    def name(self):
        return self._name

    @property
    def config(self):
        return self._storage_account.config.get_storage_container(self.name)

    @property
    def storage_container_info(self):
        if not self._storage_container_info:
            self._storage_container_info = self.az_response('storage', 'container', 'show',
                                                            '--subscription', self.subscription_id,
                                                            '--auth-mode', 'login',
                                                            '--account-name', self.storage_account_name,
                                                            '-n', self.name)
        return self._storage_container_info
