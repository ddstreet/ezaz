
from . import AzObject


class SshKey(AzObject):
    def __init__(self, name, resource_group, info=None):
        if info:
            assert info.name == name
        self._name = name
        self._resource_group = resource_group
        self._ssh_key_info = info

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
        return self._resource_group.config.get_ssh_key(self.name)

    @property
    def ssh_key_info(self):
        if not self._ssh_key_info:
            self._ssh_key_info = self.az_response('sshkey', 'show',
                                                '--subscription', self.subscription_id,
                                                '-g', self.resource_group_name,
                                                '-n', self.name)
        return self._ssh_key_info
