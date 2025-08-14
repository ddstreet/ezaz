
import importlib
import inspect
import json
import operator
import os
import subprocess

from abc import ABC
from abc import abstractmethod
from contextlib import suppress
from functools import cache
from functools import cached_property
from itertools import chain

from ..actionutil import ActionConfig
from ..argutil import ArgConfig
from ..argutil import ArgMap
from ..argutil import ArgUtil
from ..argutil import AzObjectArgConfig
from ..argutil import BoolArgConfig
from ..argutil import ConstArgConfig
from ..argutil import GroupArgConfig
from ..cache import Cache
from ..config import Config
from ..exception import AzCommandError
from ..exception import AzObjectExists
from ..exception import CacheExpired
from ..exception import CacheMiss
from ..exception import DefaultConfigNotFound
from ..exception import InvalidAzObjectName
from ..exception import NoAzObjectExists
from ..exception import NotCreatable
from ..exception import NotDeletable
from ..exception import NotDownloadable
from ..exception import NotListable
from ..exception import NotLoggedIn
from ..exception import RequiredArgumentGroup
from ..exception import UnsupportedAction
from ..filter import FILTER_ALL
from ..filter import FILTER_DEFAULT
from ..filter import Filters
from ..filter import QuickFilter
from ..response import lookup_response


class AzAction(ArgUtil, ABC):
    # For auto-importing
    EZAZ_AZOBJECT_CLASS = True

    def __init__(self, *, verbose=0, dry_run=False, **kwargs):
        super().__init__()
        self._verbose = verbose
        self._dry_run = dry_run

    @property
    def verbose(self):
        return self._verbose

    @property
    def dry_run(self):
        return self._dry_run

    def _trace(self, msg):
        if self.verbose:
            print(msg)

    @property
    def _exec_environ(cls):
        return {k: v for k, v in os.environ.items() if 'ARGCOMPLETE' not in k}

    def _args_to_cmd(self, *args, cmd_args={}, **kwargs):
        cmd = list(args)
        for k, v in cmd_args.items():
            cmd.append(k)
            if isinstance(v, list):
                cmd.extend(v)
            elif isinstance(v, bool):
                cmd.append(str(v))
            elif isinstance(v, int):
                cmd.append(str(v))
            elif v is not None:
                cmd.append(v)
        return cmd

    def _exec(self, *args, cmd_args={}, check=True, dry_runnable=True, **kwargs):
        cmd = self._args_to_cmd(*args, cmd_args=cmd_args, **kwargs)
        for c in cmd:
            if not isinstance(c, str):
                raise RuntimeError(f'cmd value not str type: {c}')
        if self.dry_run and not dry_runnable:
            print(f'DRY-RUN (not running): {" ".join(cmd)}')
            return None
        self._trace(' '.join(cmd))
        try:
            return subprocess.run(cmd, check=check, env=self._exec_environ, **kwargs)
        except subprocess.CalledProcessError as cpe:
            if cpe.stderr:
                if any(s in cpe.stderr for s in ["Please run 'az login' to setup account",
                                                 "Interactive authentication is needed"]):
                    raise NotLoggedIn()
                elif self.verbose > 1:
                    print(f'az command error: {cpe}')
            raise AzCommandError(cpe)

    def az(self, *args, capture_output=False, **kwargs):
        return self._exec('az', *args, capture_output=capture_output, **kwargs)

    def az_stdout(self, *args, **kwargs):
        cp = self.az(*args, capture_output=True, text=True, **kwargs)
        return cp.stdout if cp else ''

    def az_json(self, *args, **kwargs):
        stdout = self.az_stdout(*args, **kwargs)
        return json.loads(stdout) if stdout else {}

    def az_response(self, *args, **kwargs):
        cls = lookup_response(*args)
        j = self.az_json(*args, **kwargs)
        return cls(j) if j else None

    def az_responselist(self, *args, **kwargs):
        cls = lookup_response(*args)
        j = self.az_json(*args, **kwargs)
        return cls(j) if j else []


class CachedAzAction(AzAction):
    def __init__(self, *, cache=None, **kwargs):
        super().__init__(**kwargs)
        self._cache = cache

    @property
    def cache(self):
        return self._cache

    def az_stdout(self, *args, cmd_args={}, **kwargs):
        cmd = self._args_to_cmd(*args, cmd_args=cmd_args, **kwargs)
        if self.cache and self._is_argcomplete:
            with suppress(CacheExpired, CacheMiss):
                return self.cache.read(cmd)
        stdout = super().az_stdout(*args, cmd_args=cmd_args, **kwargs)
        if self.cache and stdout:
            self.cache.write(cmd, stdout)
        return stdout

    @property
    def _is_argcomplete(cls):
        return '_ARGCOMPLETE' in os.environ.keys()


class AzObject(CachedAzAction):
    @classmethod
    @abstractmethod
    def azobject_name_list(cls):
        pass

    @classmethod
    def azobject_name(cls, sep='_'):
        return sep.join(cls.azobject_name_list())

    @classmethod
    def azobject_text(cls):
        return cls.azobject_name(' ')

    @classmethod
    def get_common_argconfigs(cls, is_parent=False):
        return cls.get_self_id_argconfig(is_parent=is_parent)

    @classmethod
    def get_self_id_argconfig(cls, is_parent):
        return [AzObjectArgConfig(cls.azobject_name(),
                                  dest=cls.get_self_id_argconfig_dest(is_parent=is_parent),
                                  azclass=cls,
                                  help=f'Use the specified {cls.azobject_text()}, instead of the default')]

    @classmethod
    def get_self_id_argconfig_dest(cls, is_parent):
        return cls.azobject_name()

    @classmethod
    def get_action_configmap(cls):
        return {}

    @classmethod
    def get_action_names(cls):
        return list(cls.get_action_configmap().keys())

    @classmethod
    def get_action_configs(cls):
        return list(cls.get_action_configmap().values())

    @classmethod
    def get_action_config(cls, action):
        for config in cls.get_action_configs():
            if config.is_action(action):
                return config
        return None

    @classmethod
    def make_action_config(cls, action, *, cmd=None, argconfigs=None, common_argconfigs=None, is_parent=False, description=None, **kwargs):
        if cmd is None:
            try:
                cmd = getattr(cls, f'get_{action}_action_cmd')()
            except AttributeError:
                cmd = cls.get_cmd_base() + [action]
        if argconfigs is None:
            with suppress(AttributeError):
                argconfigs = getattr(cls, f'get_{action}_action_argconfigs')()
        if common_argconfigs is None:
            try:
                common_argconfigs = getattr(cls, f'get_{action}_common_argconfigs')(is_parent=is_parent)
            except AttributeError:
                common_argconfigs = cls.get_common_argconfigs(is_parent=is_parent)
        if description is None:
            with suppress(AttributeError):
                description = getattr(cls, f'get_{action}_action_description')()
        return ActionConfig(action,
                            cls=cls,
                            cmd=cmd,
                            argconfigs=(argconfigs or []) + (common_argconfigs or []),
                            description=description,
                            **kwargs)

    @classmethod
    def get_cmd_base(cls):
        return cls.azobject_name_list()

    @classmethod
    def is_child_container(cls):
        return False

    @classmethod
    def is_child(cls):
        return False

    @classmethod
    def info_id(cls, info):
        # Most use their 'name' as their obj_id
        return info.name

    @classmethod
    def create_from_opts(cls, **opts):
        if not cls.is_child():
            return cls(verbose=opts.get('verbose'),
                       dry_run=opts.get('dry_run'),
                       cache=Cache(opts.get('cache')),
                       config=Config(opts.get('config')))

        parent = cls.get_parent_class().create_from_opts(**opts)
        name = cls.azobject_name()
        return parent.get_specified_child(name, opts) or parent.get_default_child(name)

    def __init__(self, *, config, info=None, **kwargs):
        super().__init__(**kwargs)
        self._config = config

    @property
    def config(self):
        return self._config

    @cached_property
    def filters(self):
        return Filters(self.config.get_object('filters'))

    @property
    @abstractmethod
    def azobject_id(self):
        pass

    @abstractmethod
    def info(self, **opts):
        pass

    def get_argconfig_default_values(self, is_parent=False):
        return self.get_self_ids(is_parent=is_parent)

    def get_self_id(self, is_parent):
        return {self.get_self_id_argconfig_dest(is_parent=is_parent): self.azobject_id}

    def get_self_ids(self, is_parent=False):
        return self.get_self_id(is_parent=is_parent)

    @property
    def exists(self):
        try:
            self.info()
            return True
        except NoAzObjectExists:
            return False

    def do_action(self, *, actioncfg, dry_runnable=False, is_parent=False, **opts):
        if self.verbose > 2:
            print(f'do_action(actioncfg={actioncfg}, dry_runnable={dry_runnable}, opts={opts})')

        for k, v in self.get_argconfig_default_values(is_parent=is_parent).items():
            if opts.get(k) is None:
                opts[k] = v

        az = getattr(self, f'az_{actioncfg.az}', self.az)
        return az(*actioncfg.cmd, cmd_args=actioncfg.cmd_args(**opts), dry_runnable=dry_runnable)


class AzSubObject(AzObject):
    @classmethod
    def is_child(cls):
        return True

    @classmethod
    @abstractmethod
    def get_parent_class(cls):
        pass

    @classmethod
    def default_key(cls):
        return f'default_{cls.azobject_name()}'

    @classmethod
    def object_key(cls, obj_id):
        return f'{cls.azobject_name()}.{obj_id}'

    @classmethod
    def get_parent_common_argconfigs(cls):
        return cls.get_parent_class().get_common_argconfigs(is_parent=True)

    @classmethod
    def get_common_argconfigs(cls, is_parent=False):
        return (cls.get_parent_common_argconfigs() +
                super().get_common_argconfigs(is_parent=is_parent))

    def __init__(self, *, parent, azobject_id, **kwargs):
        super().__init__(**kwargs)
        self._parent = parent
        self._azobject_id = azobject_id
        assert self._parent.is_child_container()

    @property
    def azobject_id(self):
        return self._azobject_id

    @property
    def parent(self):
        return self._parent

    @property
    def cache(self):
        return self.parent.cache

    @property
    def verbose(self):
        return self.parent.verbose

    @property
    def dry_run(self):
        return self.parent.dry_run

    def get_self_ids(self, is_parent=False):
        self_id = super().get_self_ids(is_parent=is_parent)
        if self.is_child():
            return ArgMap(self.parent.get_self_ids(is_parent=True), self_id)
        return self_id


class AzSubObjectContainer(AzObject):
    @classmethod
    def is_child_container(cls):
        return True

    @classmethod
    @abstractmethod
    def get_child_classes(cls):
        pass

    @classmethod
    def get_child_classmap(cls):
        return {c.azobject_name(): c for c in cls.get_child_classes()}

    @classmethod
    def get_child_names(cls):
        return list(cls.get_child_classmap().keys())

    @classmethod
    def get_child_class(cls, name):
        with suppress(KeyError):
            return cls.get_child_classmap()[name]
        raise InvalidAzObjectName(f'AzObject {cls.__name__} does not contain AzObjects with name {name}')

    @classmethod
    def get_descendant_classes(cls):
        return (cls.get_child_classes() +
                sum([c.get_descendant_classes()
                     for c in cls.get_child_classes()
                     if c.is_child_container()], start=[]))

    def has_default_child_id(self, name):
        try:
            self.get_default_child_id(name)
            return True
        except DefaultConfigNotFound:
            return False

    def get_default_child_id(self, name):
        cls = self.get_child_class(name)
        try:
            return self.config[cls.default_key()]
        except KeyError:
            raise DefaultConfigNotFound(cls)

    def set_default_child_id(self, name, value):
        if self.config.get(self.get_child_class(name).default_key()) != value:
            self.config[self.get_child_class(name).default_key()] = value

    def del_default_child_id(self, name):
        with suppress(KeyError):
            del self.config[self.get_child_class(name).default_key()]

    def get_specified_child(self, name, opts={}):
        obj_id = opts.get(name)
        if not obj_id:
            return None
        return self.get_child(name, obj_id)

    @cache
    def get_child_cache(self, name):
        return {}

    def get_child(self, name, obj_id, info=None):
        if not obj_id in self.get_child_cache(name):
            cls = self.get_child_class(name)
            self.get_child_cache(name)[obj_id] = cls(parent=self, azobject_id=obj_id, config=self.config.get_object(cls.object_key(obj_id)), info=info)
        return self.get_child_cache(name)[obj_id]

    def get_default_child(self, name):
        return self.get_child(name, self.get_default_child_id(name))

    def get_children(self, name, opts={}):
        cls = self.get_child_class(name)
        assert issubclass(cls, AzListable)
        return list(map(lambda info: self.get_child(name, cls.info_id(info), info=info),
                        cls.list(self, **opts)))

    def filter_azobject_id(self, name, azobject_id, *, prefix=None, suffix=None, regex=None, no_filters=False):
        if not QuickFilter(prefix, suffix, regex).check(azobject_id):
            return False
        if no_filters:
            return True
        return (self.filters.check(name, azobject_id) and
                (not self.is_child() or
                 self.parent.filter_azobject_id(name, azobject_id, prefix=prefix, suffix=suffix, regex=regex)))


class AzShowable(AzObject):
    @classmethod
    def get_show_action_config(cls):
        return cls.make_action_config('show', az='response')

    @classmethod
    def get_show_action_description(cls):
        return f'Show a {cls.azobject_text()}'
 
    @classmethod
    def get_action_configmap(cls):
        return ArgMap(super().get_action_configmap(), show=cls.get_show_action_config())

    @classmethod
    def info_cache(cls):
        if not hasattr(cls, '_info_cache'):
            cls._info_cache = {}
        return cls._info_cache

    def _info(self, **opts):
        try:
            return self.do_action(actioncfg=self.get_show_action_config(), dry_runnable=True, **opts)
        except AzCommandError as aze:
            raise NoAzObjectExists(self.azobject_text(), self.azobject_id) from aze

    def info(self, **opts):
        if self.azobject_id not in self.info_cache():
            self.info_cache()[self.azobject_id] = self._info(**opts)
        return self.info_cache()[self.azobject_id]

    def show(self, **opts):
        return self.info(**opts)


class AzListable(AzSubObject):
    @classmethod
    def get_list_action_config(cls):
        return cls.make_action_config('list', az='responselist', is_parent=True)

    @classmethod
    def get_list_action_argconfigs(cls):
        return [ArgConfig('filter_prefix', noncmd=True, help=f'List only {cls.azobject_text()}s that start with the prefix'),
                ArgConfig('filter_suffix', noncmd=True, help=f'List only {cls.azobject_text()}s that end with the suffix'),
                ArgConfig('filter_regex', noncmd=True, help=f'List only {cls.azobject_text()}s that match the regular expression'),
                BoolArgConfig('-N', '--no-filters', noncmd=True, help=f'Do not use any configured filters (the --filter-* parameters will still be used)')]

    @classmethod
    def get_list_common_argconfigs(cls, is_parent=False):
        # Don't include our self id param for list action
        return [argconfig for argconfig in cls.get_common_argconfigs(is_parent=is_parent)
                if argconfig.dest != cls.get_self_id_argconfig_dest(is_parent=is_parent)]

    @classmethod
    def get_list_action_description(cls):
        return f'List {cls.azobject_text()}s'
 
    @classmethod
    def get_action_configmap(cls):
        return ArgMap(super().get_action_configmap(), list=cls.get_list_action_config())

    @classmethod
    def list(cls, parent, *, filter_prefix=None, filter_suffix=None, filter_regex=None, no_filters=False, **opts):
        if not getattr(cls, 'info_cache_complete', False):
            for info in parent.do_action(actioncfg=cls.get_list_action_config(), is_parent=True, dry_runnable=True, **opts):
                cls.info_cache()[cls.info_id(info)] = info
            cls.info_cache_complete = True

        return [info for info in cls.info_cache().values()
                if parent.filter_azobject_id(cls.azobject_name(),
                                             cls.info_id(info),
                                             prefix=filter_prefix,
                                             suffix=filter_suffix,
                                             regex=filter_regex,
                                             no_filters=no_filters)]


class AzRoActionable(AzShowable, AzListable):
    pass


# Do not ever actually call the show command, always use the list
# command.  This is appropriate for classes that don't support show,
# or have a quick list response.  This should not be used for classes
# where list is slow.
class AzEmulateShowable(AzShowable, AzListable):
    def _info(self, **opts):
        self.list(self.parent, **opts)
        with suppress(KeyError):
            return self.info_cache()[self.azobject_id]
        raise NoAzObjectExists(self.azobject_text(), self.azobject_id)


class AzCreatable(AzObject):
    @classmethod
    def get_create_action_config(cls):
        return cls.make_action_config('create')

    @classmethod
    def get_create_action_description(cls):
        return f'Create a {cls.azobject_text()}'

    @classmethod
    def get_action_configmap(cls):
        return ArgMap(super().get_action_configmap(), create=cls.get_create_action_config())

    def create(self, **opts):
        if self.exists:
            raise AzObjectExists(self.azobject_text(), self.azobject_id)
        self.do_action(actioncfg=self.get_create_action_config(), **opts)


class AzDeletable(AzObject):
    @classmethod
    def get_delete_action_config(cls):
        return cls.make_action_config('delete')

    @classmethod
    def get_delete_action_description(cls):
        return f'Delete a {cls.azobject_text()}'
 
    @classmethod
    def get_action_configmap(cls):
        return ArgMap(super().get_action_configmap(), delete=cls.get_delete_action_config())

    def delete(self, **opts):
        if not self.exists:
            raise NoAzObjectExists(self.azobject_text(), self.azobject_id)
        self.do_action(actioncfg=self.get_delete_action_config(), **opts)


class AzRwActionable(AzCreatable, AzDeletable):
    pass


class AzDefaultable(AzObject):
    # TODO - redo this. either sub-actions or split actions.

    @classmethod
    def get_default_action_config(cls):
        return cls.make_action_config('default')

    @classmethod
    def get_default_action_argconfigs(cls):
        return [GroupArgConfig(ConstArgConfig('s', 'set', const='default_set', help='Set the default'),
                               ConstArgConfig('u', 'unset', const='default_unset', help='Unset the default'),
                               ConstArgConfig('show', const='default_show', help='Show the default, if any (default)'),
                               dest='default_action')]

    @classmethod
    def get_default_action_description(cls):
        return f'Configure the default {cls.azobject_text()}'
 
    @classmethod
    def get_action_configmap(cls):
        return ArgMap(super().get_action_configmap(), default=cls.get_default_action_config())

    @classmethod
    def default(cls, parent, **opts):
        default_action = cls.get_default_action_config().cmd_args(**opts).get('default_action')
        if default_action:
            return getattr(cls, default_action)(parent, **opts)

    @classmethod
    def default_set(cls, parent, **opts):
        default_id = cls.required_arg_value(cls.azobject_name(), opts, '--set')
        parent.set_default_child_id(cls.azobject_name(), default_id)
        return f'Set default {cls.azobject_text()}: {default_id}'

    @classmethod
    def default_unset(cls, parent, **opts):
        parent.del_default_child_id(cls.azobject_name())
        return f'Unset default {cls.azobject_text()}'

    @classmethod
    def default_show(cls, parent, **opts):
        return f'Default {cls.azobject_text()}: {parent.get_default_child_id(cls.azobject_name())}'


class AzCommonActionable(AzRoActionable, AzRwActionable, AzDefaultable):
    pass


class AzFilterer(AzObject):
    @classmethod
    def get_filter_action_config(cls):
        return cls.make_action_config('filter')

    @classmethod
    def get_filter_type_groupargconfig(cls):
        return GroupArgConfig(ConstArgConfig('filter_all', const=FILTER_ALL,
                                             help=f'Configure a filter for all object types (use with caution)'),
                              *[ConstArgConfig(f'filter_{azobject_cls.azobject_name()}', const=azobject_cls.azobject_name(),
                                               help=f'Configure a filter for only {azobject_cls.azobject_text()}s')
                                for azobject_cls in cls.get_descendant_classes()],
                              ConstArgConfig('filter_default', const=FILTER_DEFAULT,
                                             help=f'Configure a default filter (use with caution)'),
                              dest='filter_type')

    @classmethod
    def get_filter_action_argconfigs(cls):
        return [cls.get_filter_type_groupargconfig(),
                GroupArgConfig(ArgConfig('--prefix', help=f'Update filter to select only object names that start with the prefix'),
                               ConstArgConfig('--no-prefix', const='', help=f'Remove prefix filter'),
                               dest='prefix'),
                GroupArgConfig(ArgConfig('--suffix', help=f'Update filter to select only object names that end with the suffix'),
                               ConstArgConfig('--no-suffix', const='', help=f'Remove suffix filter'),
                               dest='suffix'),
                GroupArgConfig(ArgConfig('--regex', help=f'Update filter to select only object names that match the regular expression'),
                               ConstArgConfig('--no-regex', const='', help=f'Remove regex filter'),
                               dest='regex')]

    @classmethod
    def get_filter_action_description(cls):
        return f"Configure the filters for this {cls.azobject_text()}'s descendant objects"

    @classmethod
    def get_action_configmap(cls):
        configmap = super().get_action_configmap()
        if cls.is_child_container():
            return ArgMap(configmap, filter=cls.get_filter_action_config())
        return configmap

    def filter(self, filter_type=None, **opts):
        for ftype in ['prefix', 'suffix', 'regex']:
            if opts.get(ftype) is not None:
                if not filter_type:
                    raise RequiredArgumentGroup(self.get_filter_type_groupargconfig().opts, self._opt_to_arg(ftype), exclusive=True)
                setattr(self.filters.get_filter(filter_type), ftype, opts.get(ftype))
        return str(self.filters)
