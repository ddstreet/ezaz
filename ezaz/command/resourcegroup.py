
from .command import SubscriptionSubCommand
from .command import StandardActionCommand


class ResourceGroupCommand(SubscriptionSubCommand, StandardActionCommand):
    ACTION_ARGUMENT_NAME = 'resource group'
    ACTION_ARGUMENT_METAVAR = 'GROUP'
    ACTION_ATTR_NAME = 'resource_group'

    @classmethod
    def name(cls):
        return 'resourcegroup'

    @classmethod
    def aliases(cls):
        return ['group', 'rg']

    def _resource_group(self, resource_group):
        return self._subscription.get_resource_group(resource_group)

    def _show(self, resource_group):
        info = resource_group.resource_group_info
        msg = info.name
        if self.verbose:
            msg += f' (location: {info.location})'
            if info.tags:
                tags = []
                for k in info.tags:
                    v = getattr(info.tags, k)
                    tags.append(k if not v else f'{k}={v}')
                msg += f' [tags: {" ".join(tags)}]'
        print(msg)

