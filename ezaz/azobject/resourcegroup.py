
import json
import subprocess

from contextlib import contextmanager

from ..exception import NotLoggedIn
from . import AzObject


class ResourceGroup(AzObject):
    @classmethod
    def name(cls):
        return 'resourcegroup'

    @classmethod
    def aliases(cls):
        return ['group', 'rg']

    @classmethod
    def _parser_add_arguments(cls, parser):
        parser.add_argument('--prefix',
                            help='Filter by name starting text')
        parser.add_argument('--suffix',
                            help='Filter by name ending text')

        title_group = parser.add_argument_group('Action', 'Action to perform (default is --show)')
        group = title_group.add_mutually_exclusive_group()
        group.add_argument('-l', '--list',
                           action='store_true',
                           help='List resource groups')
        group.add_argument('--create',
                           action='store_true',
                           help='Create a resource group')
        group.add_argument('--set',
                           action='store_true',
                           help='Set the current resource group')
        group.add_argument('--show',
                           action='store_true',
                           help='Show current resource group')

    def _filter_group(self, group):
        if self.options.prefix and not group.name.startswith(self.options.prefix):
            return False
        if self.options.suffix and not group.name.endswith(self.options.suffix):
            return False
        return True

    def _filter_groups(self, groups):
        groups = [g for g in groups if self._filter_group(g)]

    def list(self):
        responses = self.az_responselist('group', 'list')
        for response in responses:
            self._show_group(response)

    def _show_group(self, group):
        msg = group.name
        if self.verbose:
            msg += f' (location: {group.location})'
            if group.tags:
                tags = []
                for k in group.tags:
                    v = getattr(group.tags, k)
                    tags.append(k if not v else f'{k}={v}')
                msg += f' [tags: {" ".join(tags)}]'
        print(msg)

    def create(self):
        pass

    def set(self):
        pass

    def show(self):
        pass

    def run(self):
        self.list()
