
from . import AzObject


class VM(AzObject):
    def __init__(self, name, resource_group, info=None):
        if info:
            assert info.name == name
        self._name = name
        self._resource_group = resource_group
        self._vminfo = info

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
        return self._resource_group.config.get_vm(self.name)

    @property
    def vminfo(self):
        if not self._vminfo:
            self._vminfo = self.az_response('vm', 'show',
                                            '--subscription', self.subscription_id,
                                            '-g', self.resource_group_name,
                                            '-n', self.name)
        return self._vminfo
