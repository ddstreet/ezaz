
from contextlib import contextmanager
from contextlib import suppress

from ..argutil import AzObjectArgConfig
from ..exception import DefaultConfigNotFound
from .command import AzObjectCommand


class TopologyCommand(AzObjectCommand):
    @classmethod
    def command_name_list(cls):
        return ['topology']

    @classmethod
    def azclass(cls):
        from ..azobject.subscription import Subscription
        return Subscription

    @classmethod
    def parser_add_arguments(cls, parser):
        from ..azobject.subscription import Subscription
        AzObjectArgConfig(Subscription.azobject_name(), azclass=Subscription).add_to_parser(parser)

        classes = Subscription.get_descendant_classes()
        for subcls in classes:
            AzObjectArgConfig(subcls.azobject_name(), azclass=subcls).add_to_parser(parser)

        parser.add_argument('--defaults-only', action='store_true', help='Only show the default objects')

        ignore_choices = sorted([c.azobject_name() for c in classes])
        ignore_default = ['location', 'role_definition', 'role_assignment', 'storage_key']
        ignore_group = parser.add_mutually_exclusive_group()
        ignore_group.add_argument('--ignore',
                                  action='append',
                                  choices=ignore_choices,
                                  help=f'Do not show these types of objects, or their children (default: {", ".join(ignore_default)})')
        ignore_group.add_argument('--ignore-also',
                                  action='append',
                                  default=ignore_default,
                                  choices=sorted(set(ignore_choices) - set(ignore_default)),
                                  help=f'Same as --ignore, but include the defaults as well')
        ignore_group.add_argument('--ignore-none', action='store_true', help='Do not ignore any types of objects')

    @contextmanager
    def indent(self):
        self._indent += 2
        try:
            yield
        finally:
            self._indent -= 2

    @property
    def ignore(self):
        if self.options.ignore_none:
            return []
        return self.options.ignore or self.options.ignore_also

    def is_default(self, child):
        with suppress(DefaultConfigNotFound):
            return child.parent.get_default_child_id(child.azobject_name()) == child.azobject_id
        return False

    def show(self, msg):
        indent = ' ' * self._indent
        print(f'{indent}{msg}')

    def run(self):
        self._indent = 0
        self.show_azobject(self.azobject)

    def show_azobject(self, azobject):
        self.show(f'{azobject.__class__.__name__}: {azobject}')
        if not azobject.is_child_container():
            return
        for subcls in azobject.get_child_classes():
            name = subcls.azobject_name()
            if name in self.ignore:
                continue
            for child in azobject.get_children(name):
                if self.options.defaults_only and not self.is_default(child):
                    continue
                if self.opts.get(name) and self.opts.get(name) != child.azobject_id:
                    continue
                with self.indent():
                    self.show_azobject(child)
