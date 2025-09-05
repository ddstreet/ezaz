
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
                BoolArgConfig('no_filters', help='Do not use any configured filters'),
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

    @property
    def ignore(self):
        if self.options.ignore_none:
            return []
        return self.options.ignore or self.options.ignore_also

    def topology(self, **opts):
        self._indent = 0
        rootcls = self.get_root_classmap().get(opts.get('root'))
        self.show_azobject_id(None, rootcls, rootcls.get_instance(**opts).info(), opts)

    def show_azobject_id(self, parent, azclass, azobject_info, opts):
        print(f'{self.tab}{azclass.__name__}: {azobject_info}')
        if not azclass.has_child_classes():
            return
        if parent:
            azobject = parent.get_child(azclass.azobject_name(), azobject_info._id)
        else:
            azobject = azclass.get_instance(**opts)
        for subcls in azclass.get_child_classes():
            name = subcls.azobject_name()
            if name in self.ignore:
                continue
            for child_info in azobject.get_null_child(name).list(**opts):
                if self.options.defaults_only and child_info._id != azobject.get_default_child_id(name):
                    continue
                if self.opts.get(name) and self.opts.get(name) != child_info._id:
                    continue
                with self.indent():
                    self.show_azobject_id(azobject, subcls, child_info, opts)
