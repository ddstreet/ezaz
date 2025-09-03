
from contextlib import contextmanager
from contextlib import suppress

from itertools import chain

from ..argutil import ArgMap
from ..argutil import AzObjectArgConfig
from ..argutil import BoolArgConfig
from ..argutil import ChoiceMapArgConfig
from ..argutil import ChoicesArgConfig
from ..argutil import ExclusiveGroupArgConfig
from ..exception import DefaultConfigNotFound
from .command import SimpleCommand


class TopologyCommand(SimpleCommand):
    @classmethod
    def command_name_list(cls):
        return ['topology']

    @classmethod
    def get_root_classmap(cls):
        from ..azobject.user import User
        return ArgMap(user=User, **{c.azobject_name(): c for c in User.get_descendant_classes()})

    @classmethod
    def get_simple_command_argconfigs(cls):
        from ..azobject.user import User
        classmap = cls.get_root_classmap()
        classnames = sorted(set(classmap.keys()) - set('user'))
        ignore_default = ['location', 'role_definition', 'role_assignment', 'storage_key', 'sku']

        return [*super().get_simple_command_argconfigs(),
                ChoiceMapArgConfig('root',
                                   choicemap=classmap,
                                   default=User.azobject_name(),
                                   help='Show the topology starting at this root object'),
                *User.get_descendant_azobject_id_argconfigs(help='Only show the specified {azobject_text} object'),
                BoolArgConfig('defaults_only', help='Only show the default objects'),
                ExclusiveGroupArgConfig(ChoicesArgConfig('ignore',
                                                         multiple=True,
                                                         choices=classnames,
                                                         default=ignore_default,
                                                         help=f'Do not show these types of objects, or their children (default: {", ".join(ignore_default)})'),
                                        ChoicesArgConfig('ignore_also',
                                                         multiple=True,
                                                         choices=sorted(set(classnames) - set(ignore_default)),
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
    def tab(self):
        return ' ' * self._indent

    @property
    def ignore(self):
        if self.options.ignore_none:
            return []
        return self.options.ignore or self.options.ignore_also

    def topology(self, **opts):
        self._indent = 0
        rootcls = self.get_root_classmap().get(opts.get('root'))
        self.show_azobject(rootcls.get_instance(**opts))

    def show_azobject(self, azobject):
        print(f'{self.tab}{azobject.__class__.__name__}: {azobject}')
        if not azobject.has_child_classes():
            return
        for subcls in azobject.get_child_classes():
            name = subcls.azobject_name()
            if name in self.ignore:
                continue
            for child in azobject.get_children(name):
                if self.options.defaults_only and not child.is_default:
                    continue
                if self.opts.get(name) and self.opts.get(name) != child.azobject_id:
                    continue
                with self.indent():
                    self.show_azobject(child)
