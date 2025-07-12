
from ..azobject.account import Account
from .command import Command


class ResourceGroupCommand(Command):
    @classmethod
    def name(cls):
        return 'resourcegroup'

    @classmethod
    def aliases(cls):
        return ['group', 'rg']

    @classmethod
    def _parser_add_arguments(cls, parser):
        parser.add_argument('--subscription',
                            help='Use the specified subscription, instead of the current subscription')

        title_group = parser.add_argument_group('Action', 'Action to perform (default is --show)')
        group = title_group.add_mutually_exclusive_group()
        group.add_argument('--create',
                           help='Create a resource group')
        group.add_argument('--list',
                           action='store_true',
                           help='List resource groups')
        group.add_argument('--clear',
                           action='store_true',
                           help='Clear the current resource group')
        group.add_argument('--set',
                           help='Set the current resource group')
        group.add_argument('--show',
                           action='store_true',
                           help='Show current resource group')

    def _setup(self):
        self._account = Account(self._config)

    @property
    def _subscription(self):
        if self._options.subscription:
            return self._account.get_subscription(self._options.subscription)
        else:
            return self._account.get_current_subscription()

    def _resource_group(self, resource_group):
        return self._subscription.get_resource_group(resource_group)

    def _run(self):
        if self._options.list:
            self.list()
        elif self._options.clear:
            self.clear()
        elif self._options.set:
            self.set(self._options.set)
        else: # default
            self.show()

    def _filter_group(self, group):
        if self._options.prefix and not group.name.startswith(self._options.prefix):
            return False
        if self._options.suffix and not group.name.endswith(self._options.suffix):
            return False
        return True

    def _filter_groups(self, groups):
        groups = [g for g in groups if self._filter_group(g)]

    def clear(self):
        del self._subscription.current_resource_group

    def set(self, resource_group):
        self._subscription.current_resource_group = resource_group

    def list(self):
        for resource_group in self._subscription.get_resource_groups():
            self._show_group(resource_group)

    def show(self):
        self._show_group(self._subscription.get_current_resource_group())

    def _show_group(self, resource_group):
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

