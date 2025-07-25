
from ..azobject.resourcegroup import ResourceGroup
from .command import AllActionCommand
from .subscription import SubscriptionCommand


class ResourceGroupCommand(AllActionCommand):
    @classmethod
    def parent_command_cls(cls):
        return SubscriptionCommand

    @classmethod
    def azobject_class(cls):
        return ResourceGroup

    @classmethod
    def aliases(cls):
        return ['group', 'rg']

    @classmethod
    def parser_add_common_arguments(cls, parser):
        super().parser_add_common_arguments(parser)
        parser.add_argument('--location',
                            help='Location (required for --create)')

    def show(self):
        info = self.azobject.info
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
