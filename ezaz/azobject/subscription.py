
from . import AzObject
from .resourcegroup import ResourceGroup


class Subscription(AzObject):
    def __init__(self, sid, account, info=None):
        if info:
            assert info.id == sid
        self._sid = sid
        self._account = account
        self._subscription_info = info

    @property
    def subscription_id(self):
        return self._sid

    @property
    def config(self):
        return self._account.config.get_subscription(self.subscription_id)

    @property
    def subscription_info(self):
        if not self._subscription_info:
            self._subscription_info = self.az_response('account', 'show', '--subscription', self.subscription_id)
        return self._subscription_info

    @property
    def current_resource_group(self):
        return self.config.current_resource_group

    @current_resource_group.setter
    def current_resource_group(self, resource_group):
        if self.current_resource_group != resource_group:
            self.config.current_resource_group = resource_group

    def get_resource_group(self, resource_group, info=None):
        return ResourceGroup(resource_group, self, info=info)

    def get_current_resource_group(self):
        return self.get_resource_group(self.current_resource_group)

    def get_resource_groups(self):
        return [self.get_resource_group(info.name, info=info)
                for info in self.az_responselist('group', 'list',
                                                 '--subscription', self.subscription_id)]
