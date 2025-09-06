
import json

from ..argutil import AzClassDescendantsChoicesArgConfig
from ..argutil import BoolArgConfig
from ..argutil import ChoicesArgConfig
from ..argutil import ConstArgConfig
from ..argutil import GroupArgConfig
from ..argutil import TimeDeltaArgConfig
from ..argutil import ExclusiveGroupArgConfig
from ..exception import DefaultConfigNotFound
from ..exception import RequiredArgument
from ..exception import RequiredArgumentGroup
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
                cls.make_action_config('set-expiry',
                                       func='set_expiry',
                                       description='Set cache expiry duration',
                                       argconfigs=cls.get_set_action_argconfigs())]

    @classmethod
    def get_show_action_argconfigs(cls):
        return [*cls.azclass().get_descendant_azobject_id_argconfigs()]

    @classmethod
    def get_set_action_argconfigs(cls):
        return [GroupArgConfig(*cls.azclass().get_descendant_azobject_id_argconfigs(),
                               title='Resource options'),
                GroupArgConfig(BoolArgConfig('default_config',
                                             help='Configure the default cache configuration'),
                               AzClassDescendantsChoicesArgConfig('config_location',
                                                                  include_self=True,
                                                                  azclass=cls.azclass(),
                                                                  metavar='RESOURCE_NAME',
                                                                  help='Configure the cache configuration on this object type (must be same as or ancestor of --type)'),
                               AzClassDescendantsChoicesArgConfig('type',
                                                                  dest='object_type',
                                                                  include_self=True,
                                                                  azclass=cls.azclass(),
                                                                  metavar='RESOURCE_NAME',
                                                                  help='The type of object to cache (must be same as or descendant of --config-location)'),
                               title='Configuration scope options'),
                ExclusiveGroupArgConfig(TimeDeltaArgConfig('show_cache_duration', help="How long to use cached 'show' command info"),
                                        ConstArgConfig('show_cache_disable', const='nocache', help="Disable caching of 'show' command info"),
                                        ConstArgConfig('show_cache_forever', const='forever', help="Cache 'show' command info forever"),
                                        ConstArgConfig('show_cache_none', const='none', help="Remove cache configuration for 'show' command info"),
                                        cmddest='show_expiry',
                                        title='Show command caching options'),
                ExclusiveGroupArgConfig(TimeDeltaArgConfig('list_cache_duration', help="How long to use cached 'list' command info"),
                                        ConstArgConfig('list_cache_disable', const='nocache', help="Disable caching of 'list' command info"),
                                        ConstArgConfig('list_cache_forever', const='forever', help="Cache 'list' command info forever"),
                                        ConstArgConfig('list_cache_none', const='none', help="Remove cache configuration for 'list' command info"),
                                        cmddest='list_expiry',
                                        title='List command caching options')]

    def show(self, **opts):
        self._indent = 0
        default_expiry = self.azclass().get_instance(**opts).default_cache_expiry()
        print(f"[Defaults: {self.expirystr(default_expiry)}]")
        with self.indent():
            self.show_azclass(self.azclass(), opts)

    def show_azclass(self, azclass, opts):
        if not azclass.has_child_classes():
            return

        try:
            azobject = azclass.get_instance(**opts)
        except DefaultConfigNotFound:
            return

        print(f'{self.tab}{azclass.__name__}: {azobject.azobject_id}')
        expiries = [f'{c.__name__}: {self.expirystr(expiry)}'
                    for c in azclass.get_descendant_classes()
                    for expiry in [azobject.cache_expiry(c.azobject_name())]
                    if expiry]
        if expiries:
            print(f'{self.tab}[{", ".join(expiries)}]')
        else:
            print(f'{self.tab}[No cache config]')

        for child_class in azclass.get_child_classes():
            with self.indent():
                self.show_azclass(child_class, opts)

    def set_expiry(self, default_config, config_location, object_type, **opts):
        if not any((default_config, config_location)):
            raise RequiredArgumentGroup(['default_config', 'config_location'], 'set-expiry', exclusive=True)

        if all((default_config, object_type)):
            raise ArgumentError(f'Cannot use --config-location with --defualt-config')

        if config_location:
            if not object_type:
                raise RequiredArgument('object_type', '--config-location')
            config_location_azclass = self.azclass().get_descendant_classmap(include_self=True).get(config_location)
            object_type_azclass = self.azclass().get_descendant_classmap(include_self=True).get(object_type)
            if config_location != object_type and not config_location_azclass.is_ancestor_class(object_type_azclass):
                raise ArgumentError(f"--config-location '{config_location}' not same as or ancestor of --object-type '{object_type}'")
        
        show_expiry = self.get_action_config('set-expiry').cmd_opts(**opts).get('show_expiry')
        list_expiry = self.get_action_config('set-expiry').cmd_opts(**opts).get('list_expiry')
        if not show_expiry and not list_expiry:
            raise RequiredArgumentGroup(['show_expiry', 'list_expiry'], 'set-expiry', exclusive=False)

        if default_config:
            self.set_default_config(self.azclass(), show_expiry, list_expiry, opts)
        else:
            assert self.set_azclass_expiry(self.azclass(), config_location, object_type, show_expiry, list_expiry, opts)

    def set_azclass_expiry(self, azclass, config_location, object_type, show_expiry, list_expiry, opts):
        if azclass.azobject_name() == config_location:
            azobject = azclass.get_instance(**opts)
            expiry = self.set_expiry_attrs(azobject.cache_expiry(object_type), show_expiry, list_expiry)
            print(f'Set {config_location} id {azobject.azobject_id} cache config for {object_type} objects to: {self.expirystr(expiry)}')
            return True

        if not azclass.has_child_classes():
            return False

        for child_class in azclass.get_child_classes():
            if self.set_azclass_expiry(child_class, config_location, object_type, show_expiry, list_expiry, opts):
                return True

        return False

    def set_default_config(self, azclass, show_expiry, list_expiry, opts):
        expiry = self.set_expiry_attrs(azclass.get_instance(**opts).default_cache_expiry(), show_expiry, list_expiry)
        print(f'Set default cache config to: {self.expirystr(expiry)}')

    def set_expiry_attrs(self, expiry, show_expiry, list_expiry):
        if show_expiry is not None:
            expiry.show_expiry = None if show_expiry == 'none' else show_expiry
        if list_expiry is not None:
            expiry.list_expiry = None if list_expiry == 'none' else list_expiry
        return expiry

    def expirystr(self, expiry, none='No configuration'):
        return expiry._jsonstr() if expiry else none
