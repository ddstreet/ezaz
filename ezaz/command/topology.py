
from contextlib import suppress

from itertools import chain

from ..argutil import ArgMap
from ..argutil import AzObjectArgConfig
from ..argutil import BoolArgConfig
from ..argutil import ChoiceMapArgConfig
from ..argutil import ChoicesArgConfig
from ..argutil import ExclusiveGroupArgConfig
from ..argutil import GroupArgConfig
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
                GroupArgConfig(ChoiceMapArgConfig('root',
                                                  choicemap=classmap,
                                                  default=User.azobject_name(),
                                                  help='Show the topology starting at this root object'),
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
                                                                     help='Do not ignore any types of objects')),
                               title='Object type selection options'),
                GroupArgConfig(*User.get_descendant_azobject_id_argconfigs(help='Only show the specified {azobject_text} object'),
                               BoolArgConfig('defaults_only', help='Only show the default objects'),
                               BoolArgConfig('object_type_only', help='Only show the object type'),
                               BoolArgConfig('no_filters', help='Do not use any configured filters'),
                               title='Object instance selection options')]

    @property
    def ignore(self):
        if self.options.ignore_none:
            return []
        return self.options.ignore or self.options.ignore_also

    def topology(self, object_type_only=False, **opts):
        self._indent = 0
        rootcls = self.get_root_classmap().get(opts.get('root'))
        if object_type_only:
            rootcls.for_each_descendant_class(self.show_topology_classes,
                                              opts,
                                              context_manager=self.indent,
                                              include_self=True)
        else:
            rootinstance = rootcls.get_instance(**opts)
            rootinstance.for_each_descendant_instance(self.show_topology_instances,
                                                      opts,
                                                      context_manager=self.indent,
                                                      include_self=True)

    def show_topology_classes(self, cls, opts):
        if cls.azobject_name() in self.ignore:
            return
        print(f'{self.tab}{cls.__name__}')

    def show_topology_instances(self, instance, opts):
        if instance.azobject_name() in self.ignore:
            raise StopIteration()
        if self.options.defaults_only and not instance.is_default:
            raise StopIteration()
        specified_id = instance.get_azobject_id_from_opts(opts)
        if specified_id and specified_id != instance.azobject_id:
            raise StopIteration()
        print(f'{self.tab}{instance.__class__.__name__}: {instance.info()}')
