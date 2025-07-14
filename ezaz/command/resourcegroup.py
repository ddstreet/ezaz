
from .command import SubscriptionSubCommand


class ResourceGroupCommand(SubscriptionSubCommand):
    @classmethod
    def _cls_type_list(cls):
        return ['resource', 'group']

    @classmethod
    def aliases(cls):
        return ['group', 'rg']

    def _show(self, resource_group):
        info = resource_group.info
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

