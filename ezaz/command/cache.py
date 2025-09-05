
from ..argutil import AzClassDescendantsChoicesArgConfig
from ..argutil import ChoicesArgConfig
from ..argutil import ConstArgConfig
from ..argutil import ExclusiveGroupArgConfig
from .command import AzObjectActionCommand


class CacheCommand(AzObjectActionCommand):
    @classmethod
    def command_name_list(cls):
        return ['cache']

    @classmethod
    def azclass(cls):
        from ..azobject.user import User
        return User

    @classmethod
    def get_action_configs(cls):
        return [cls.make_action_config('show',
                                       description='Show cache',
                                       argconfigs=cls.get_show_action_argconfigs()),
                cls.make_action_config('set',
                                       description='Set cache',
                                       argconfigs=cls.get_set_action_argconfigs()),
                cls.make_action_config('clear',
                                       description='Clear cache',
                                       argconfigs=cls.get_clear_action_argconfigs())]

    @classmethod
    def get_show_action_argconfigs(cls):
        return [*cls.azclass().get_descendant_azobject_id_argconfigs()]

    @classmethod
    def get_azclass_descendants_argconfigs(cls):
        return AzClassDescendantsChoicesArgConfig('type',
                                                  dest='object_type',
                                                  azclass=cls.azclass(),
                                                  required=True,
                                                  help='The type of object to cache')

    @classmethod
    def get_set_action_argconfigs(cls):
        return [*cls.azclass().get_descendant_azobject_id_argconfigs(),
                cls.get_azclass_descendants_argconfigs()]

    @classmethod
    def get_clear_action_argconfigs(cls):
        return [*cls.azclass().get_descendant_azobject_id_argconfigs(),
                cls.get_azclass_descendants_argconfigs(),
                ExclusiveGroupArgConfig(ChoicesArgConfig('remove',
                                                         choices=['prefix', 'suffix', 'regex'],
                                                         default=[],
                                                         multiple=True,
                                                         help='Which filters to remove'),
                               ConstArgConfig('all',
                                              dest='remove',
                                              const=['all'],
                                              help='Remove the prefix, suffix, and regex filters'))]

    def show(self, **opts):
        self._indent = 0
        self.show_azclass(self.azclass(), opts)

    def show_azclass(self, azclass, opts):
        if not azclass.has_child_classes():
            return

        azobject_id = azclass.get_azobject_id_from_opts(opts)
        if not azobject_id:
            try:
                azobject_id = azclass.get_default_azobject_id(**opts)
            except DefaultConfigNotFound:
                return

        print(f'{self.tab}{azclass.__name__}: {azobject_id}')
        cacheconfigs = [f'{c.__name__}: {c.get_filter(**opts)}' for c in azclass.get_child_classes() if c.get_filter(**opts)]
        if any(filters):
            print(f'{self.tab}[{", ".join(filters)}]')
        else:
            print(f'{self.tab}[No filters]')

        for child_class in azclass.get_child_classes():
            with self.indent():
                self.show_azclass(child_class, opts)

    def set(self, object_type, prefix, suffix, regex, full, **opts):
        self.set_azclass(self.azclass(), object_type, prefix, suffix, regex, full, opts)

    def set_azclass(self, azclass, object_type, prefix, suffix, regex, full, opts):
        if not azclass.has_child_classes():
            return False

        for child_class in azclass.get_child_classes():
            if child_class.azobject_name() == object_type:
                parent = azclass.get_instance(**opts)
                f = dict(**({'prefix': prefix} if prefix or full else {}),
                         **({'suffix': suffix} if suffix or full else {}),
                         **({'regex': regex} if regex or full else {}))
                parent.set_child_filter(object_type, f)
                print(f'Set {azclass.__name__}({parent.azobject_id}) {child_class.azobject_text()} filter to {f}')
                return True

            if self.set_azclass(child_class, object_type, prefix, suffix, regex, full, opts):
                return True

        return False

    def unset(self, object_type, remove, **opts):
        self.unset_azclass(self.azclass(), object_type, remove, opts)

    def unset_azclass(self, azclass, object_type, remove, opts):
        if not azclass.has_child_classes():
            return False

        for child_class in azclass.get_child_classes():
            if child_class.azobject_name() == object_type:
                parent = azclass.get_instance(**opts)
                if 'all' in remove:
                    parent.del_child_filter(object_type)
                else:
                    f = parent.get_child_filter(object_type)
                    if 'prefix' in remove:
                        del f.prefix
                    if 'suffix' in remove:
                        del f.suffix
                    if 'regex' in remove:
                        del f.regex
                print(f'Unset {azclass.__name__}({parent.azobject_id}) {child_class.azobject_text()} filter to {parent.get_child_filter(object_type)}')
                return True

            if self.unset_azclass(child_class, object_type, remove, opts):
                return True

        return False
