
import json

from ..argutil import AzClassDescendantsChoicesArgConfig
from ..argutil import ChoicesArgConfig
from ..argutil import ConstArgConfig
from ..argutil import TimeDeltaArgConfig
from ..argutil import ExclusiveGroupArgConfig
from ..exception import DefaultConfigNotFound
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
    def get_set_action_argconfigs(cls):
        return [*cls.azclass().get_descendant_azobject_id_argconfigs(),
                AzClassDescendantsChoicesArgConfig('object_type',
                                                   dest='object_type',
                                                   include_self=True,
                                                   azclass=cls.azclass(),
                                                   required=True,
                                                   help='The type of object to cache'),
                AzClassDescendantsChoicesArgConfig('target',
                                                   dest='target',
                                                   include_self=True,
                                                   azclass=cls.azclass(),
                                                   required=True,
                                                   help='Where to attach the cache config'),
                TimeDeltaArgConfig('show_expiry', help="How long to use cached 'show' command info"),
                TimeDeltaArgConfig('list_expiry', help="How long to use cached 'list' command info")]

    @classmethod
    def get_clear_action_argconfigs(cls):
        return [*cls.azclass().get_descendant_azobject_id_argconfigs(),
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

        try:
            azobject = azclass.get_instance(**opts)
        except DefaultConfigNotFound:
            return

        print(f'{self.tab}{azclass.__name__}: {azobject.azobject_id}')
        expiries = []
        for c in azclass.get_descendant_classes():
            expiry = azobject.cache_expiry(c.azobject_name())
            if expiry:
                msg = []
                if expiry.list_expiry:
                    msg.append(f'list={expiry.list_expiry}')
                if expiry.show_expiry:
                    msg.append(f'show={expiry.show_expiry}')
                expiries.append(c.__name__ + ': (' + ','.join(msg) + ')')
        if expiries:
            print(f'{self.tab}[{", ".join(expiries)}]')
        else:
            print(f'{self.tab}[No cache config]')

        for child_class in azclass.get_child_classes():
            with self.indent():
                self.show_azclass(child_class, opts)

    def set(self, object_type, target, **opts):
        show_expiry = self.get_action_config('set').get_argconfig('show_expiry').cmd_arg_value(**opts)
        list_expiry = self.get_action_config('set').get_argconfig('list_expiry').cmd_arg_value(**opts)
        if not show_expiry and not list_expiry:
            raise RequiredArgumentGroup(['show_expiry', 'list_expiry'], 'set', exclusive=False)
        self.set_azclass(self.azclass(), object_type, target, show_expiry, list_expiry, opts)

    def set_azclass(self, azclass, object_type, target, show_expiry, list_expiry, opts):
        if azclass.azobject_name() == target:
            azobject = azclass.get_instance(**opts)
            expiry = azobject.cache_expiry(object_type)
            if show_expiry is not None:
                expiry.show_expiry = show_expiry
            if list_expiry is not None:
                expiry.list_expiry = list_expiry
            return True

        if not azclass.has_child_classes():
            return False

        for child_class in azclass.get_child_classes():
            if self.set_azclass(child_class, object_type, target, show_expiry, list_expiry, opts):
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
