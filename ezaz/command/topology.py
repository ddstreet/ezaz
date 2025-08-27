
from contextlib import contextmanager
from contextlib import suppress

from itertools import chain

from ..argutil import AzObjectArgConfig
from ..argutil import BoolArgConfig
from ..argutil import ChoicesArgConfig
from ..argutil import GroupArgConfig
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
    def get_simple_command_argconfigs(cls):
        classes = cls.azclass().get_descendant_classes()
        ignore_choices = sorted([c.azobject_name() for c in classes])
        ignore_default = ['location', 'role_definition', 'role_assignment', 'storage_key']

        return [*super().get_simple_command_argconfigs(),
                *chain(*[c.get_self_id_argconfigs(help=f'Show only specified {c.azobject_text()}') for c in classes]),
                BoolArgConfig('defaults_only', help='Only show the default objects'),
                GroupArgConfig(ChoicesArgConfig('ignore',
                                                multiple=True,
                                                choices=ignore_choices,
                                                default=ignore_default,
                                                help=f'Do not show these types of objects, or their children (default: {", ".join(ignore_default)})'),
                               ChoicesArgConfig('ignore_also',
                                                multiple=True,
                                                choices=sorted(set(ignore_choices) - set(ignore_default)),
                                                default=[],
                                                help=f'Same as --ignore, but include the defaults as well'),
                               BoolArgConfig('ignore_none',
                                             help='Do not ignore any types of objects'))]

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

    def topology(self, **opts):
        self._indent = 0
        self.show_azobject(self.azobject)

    def show_azobject(self, azobject):
        self.show(f'{azobject.__class__.__name__}: {azobject}')
        if not azobject.has_child_classes():
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
