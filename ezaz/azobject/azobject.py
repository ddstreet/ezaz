
import importlib
import inspect
import json
import operator
import os
import subprocess

from abc import ABC
from abc import abstractmethod
from contextlib import suppress
from functools import cached_property
from itertools import chain

from ..actionutil import ActionConfig
from ..actionutil import ActionHandler
from ..argutil import ArgConfig
from ..argutil import ArgMap
from ..argutil import ArgUtil
from ..argutil import BoolArgConfig
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
from ..exception import UnsupportedAction
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
                cmd += v
            if v is not None:
                cmd.append(v)
        return cmd

    def _exec(self, *args, cmd_args={}, check=True, dry_runnable=True, **kwargs):
        cmd = self._args_to_cmd(*args, cmd_args=cmd_args, **kwargs)
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
        if self.verbose > 1:
            print(f'az_stdout: {cp.stdout}')
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
        return [ArgConfig(cls.azobject_name(),
                          dest=cls.get_self_id_argconfig_dest(is_parent=is_parent),
                          completer=AzObjectCompleter(cls),
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
    def make_action_config(cls, action, *, handler_fn=None, argconfigs=[], is_parent=False, **kwargs):
        return ActionConfig(action,
                            handler=cls.make_action_handler(handler_fn or getattr(cls, cls._arg_to_opt(action))),
                            argconfigs=argconfigs + cls.get_common_argconfigs(is_parent=is_parent),
                            **kwargs)

    @classmethod
    def make_action_handler(cls, func):
        if inspect.ismethod(func):
            return AzClassActionHandler(func)
        else:
            return AzObjectActionHandler(func)

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

    def __init__(self, *, config, info=None, **kwargs):
        super().__init__(**kwargs)
        self._config = config
        self._info = info

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
    def get_info(self, **opts):
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
            self.get_info()
            return True
        except NoAzObjectExists:
            return False

    def do_action(self, *, action=None, actioncfg=None, dry_runnable=False, is_parent=False, **opts):
        if self.verbose > 2:
            print(f'do_action(action={action}, actioncfg={actioncfg}, dry_runnable={dry_runnable}, opts={opts})')
        if not actioncfg:
            print(f'FIXME: do_action without actioncfg, action {action}')
            if not action:
                raise RuntimeError('Missing both action and actioncfg')
            actioncfg = self.get_action_config(action)
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
    def get_common_argconfigs(cls, is_parent=False):
        return (cls.get_parent_class().get_common_argconfigs(is_parent=True) +
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
    def get_descendants(cls):
        return (cls.get_child_classes() +
                sum([c.get_descendants()
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

    def get_specified_child(self, name, **opts):
        obj_id = opts.get(name)
        if not obj_id:
            return None
        return self.get_child(name, obj_id)

    def get_child(self, name, obj_id, info=None):
        cls = self.get_child_class(name)
        return cls(parent=self, azobject_id=obj_id, config=self.config.get_object(cls.object_key(obj_id)), info=info)

    def get_default_child(self, name):
        return self.get_child(name, self.get_default_child_id(name))

    def get_children(self, name, **opts):
        cls = self.get_child_class(name)
        return list(map(lambda info: self.get_child(name, cls.info_id(info), info=info),
                        cls.list(self, **opts)))

    def filter_azobject_id(self, name, azobject_id, prefix=None, suffix=None, regex=None, no_filters=False, **opts):
        if not QuickFilter(prefix, suffix, regex).check(azobject_id):
            return False
        if no_filters:
            return True
        return (self.filters.check(name, azobject_id) and
                (not self.is_child() or
                 self.parent.filter_azobject_id(name, azobject_id, prefix=prefix, suffix=suffix, regex=regex, **opts)))


class AzShowable(AzObject):
    @classmethod
    def get_show_action_config(cls):
        return cls.make_action_config('show',
                                      cmd=cls.get_show_action_cmd(),
                                      argconfigs=cls.get_show_action_argconfigs(),
                                      description=cls.get_show_action_description(),
                                      az='response')

    @classmethod
    def get_show_action_cmd(cls):
        return cls.get_cmd_base() + ['show']

    @classmethod
    def get_show_action_argconfigs(cls):
        return []

    @classmethod
    def get_show_action_description(cls):
        return f'Show a {cls.azobject_text()}'
 
    @classmethod
    def get_action_configmap(cls):
        return ArgMap(super().get_action_configmap(), show=cls.get_show_action_config())

    def _get_info(self, **opts):
        opts['actioncfg'] = self.get_show_action_config()
        return self.do_action(dry_runnable=True, **opts)

    def get_info(self, **opts):
        if not self._info:
            try:
                self._info = self._get_info(**opts)
            except AzCommandError as aze:
                raise NoAzObjectExists(self.azobject_text(), self.azobject_id) from aze
        return self._info

    @property
    def info(self):
        print('info called, remove!')
        return self.get_info()

    def show(self, **opts):
        return self.get_info(**opts)


class AzListable(AzSubObject):
    @classmethod
    def get_list_action_config(cls):
        return cls.make_action_config('list',
                                      cmd=cls.get_list_action_cmd(),
                                      argconfigs=cls.get_list_action_argconfigs(),
                                      description=cls.get_list_action_description(),
                                      az='responselist',
                                      is_parent=True)

    @classmethod
    def get_list_action_cmd(cls):
        return cls.get_cmd_base() + ['list']

    @classmethod
    def get_list_action_argconfigs(cls):
        return [ArgConfig('filter_prefix', noncmd=True, help=f'List only {cls.azobject_text()}s that start with the prefix'),
                ArgConfig('filter_suffix', noncmd=True, help=f'List only {cls.azobject_text()}s that end with the suffix'),
                ArgConfig('filter_regex', noncmd=True, help=f'List only {cls.azobject_text()}s that match the regular expression'),
                BoolArgConfig('-N', '--no-filters', noncmd=True, help=f'Do not use any configured filters (the --filter-* parameters will still be used)')]

    @classmethod
    def get_list_action_description(cls):
        return f'List {cls.azobject_text()}s'
 
    @classmethod
    def get_action_configmap(cls):
        return ArgMap(super().get_action_configmap(), list=cls.get_list_action_config())

    @classmethod
    def list(cls, parent, filter_prefix=None, filter_suffix=None, filter_regex=None, no_filters=False, **opts):
        opts['actioncfg'] = cls.get_list_action_config()
        opts['prefix'] = filter_prefix
        opts['suffix'] = filter_suffix
        opts['regex'] = filter_regex
        opts['no_filters'] = no_filters
        return list(filter(lambda info: parent.filter_azobject_id(cls.azobject_name(), cls.info_id(info), **opts),
                           parent.do_action(is_parent=True, **opts)))

class AzCreatable(AzObject):
    @classmethod
    def get_create_action_config(cls):
        return cls.make_action_config('create',
                                      cmd=cls.get_create_action_cmd(),
                                      argconfigs=cls.get_create_action_argconfigs(),
                                      description=cls.get_create_action_description())

    @classmethod
    def get_create_action_cmd(cls):
        return cls.get_cmd_base() + ['create']

    @classmethod
    def get_create_action_argconfigs(cls):
        return []

    @classmethod
    def get_create_action_description(cls):
        return f'Create a {cls.azobject_text()}'

    @classmethod
    def get_action_configmap(cls):
        return ArgMap(super().get_action_configmap(), create=cls.get_create_action_config())

    def create(self, **opts):
        if self.exists:
            raise AzObjectExists(self.azobject_text(), self.azobject_id)
        opts['actioncfg'] = self.get_create_action_config()
        self.do_action(**opts)


class AzDeletable(AzObject):
    @classmethod
    def get_delete_action_config(cls):
        return cls.make_action_config('delete',
                                      cmd=cls.get_delete_action_cmd(),
                                      argconfigs=cls.get_delete_action_argconfigs(),
                                      description=cls.get_delete_action_description())

    @classmethod
    def get_delete_action_cmd(cls):
        return cls.get_cmd_base() + ['delete']

    @classmethod
    def get_delete_action_argconfigs(cls):
        return []

    @classmethod
    def get_delete_action_description(cls):
        return f'Delete a {cls.azobject_text()}'
 
    @classmethod
    def get_action_configmap(cls):
        return ArgMap(super().get_action_configmap(), delete=cls.get_delete_action_config())

    def delete(self, **opts):
        if not self.exists:
            raise NoAzObjectExists(self.azobject_text(), self.azobject_id)
        opts['actioncfg'] = self.get_delete_action_config()
        self.do_action(**opts)


class AzRoActionable(AzShowable, AzListable):
    pass


class AzRwActionable(AzCreatable, AzDeletable):
    pass


class AzDefaultable(AzObject):
    @classmethod
    def get_default_action_config(cls):
        return cls.make_action_config('default',
                                      argconfigs=cls.get_default_action_argconfigs(),
                                      description=cls.get_default_action_description())

    @classmethod
    def get_default_action_argconfigs(cls):
        return [GroupArgConfig(BoolArgConfig('s', 'set', help='Set the default'),
                               BoolArgConfig('r', 'remove', help='Remove the current default'))]

    @classmethod
    def get_default_action_description(cls):
        return f'Configure the default {cls.azobject_text()}'
 
    @classmethod
    def get_action_configmap(cls):
        return ArgMap(super().get_action_configmap(), default=cls.get_default_action_config())

    @classmethod
    def default(cls, parent, set=False, remove=False, **opts):
        if set:
            default_id = cls.required_arg_value(cls.azobject_name(), opts, '--set')
            parent.set_default_child_id(cls.azobject_name(), default_id)
            return f'Set default {cls.azobject_text()}: {default_id}'
        elif remove:
            parent.del_default_child_id(cls.azobject_name())
            return f'Unset default {cls.azobject_text()}'
        return f'Default {cls.azobject_text()}: {parent.get_default_child_id(cls.azobject_name())}'


class AzCommonActionable(AzRoActionable, AzRwActionable, AzDefaultable):
    pass


class AzObjectCompleter:
    def __init__(self, azclass):
        self.azclass = azclass

    def get_list_action_config(self):
        # The actual cmdline may have a different action; we need to override with the list action
        return self.azclass.get_action_config('list')

    def get_instance(self, azclass, parsed_args):
        if azclass.is_child():
            parent = self.get_instance(azclass.get_parent_class(), parsed_args)
            name = azclass.azobject_name()
            return parent.get_specified_child(name, **vars(parsed_args)) or parent.get_default_child(name)
        return azclass(cache=Cache(), config=Config(), is_parent=True, options=parsed_args)

    def __call__(self, *, prefix, action, parser, parsed_args, **kwargs):
        try:
            parent = self.get_instance(self.azclass.get_parent_class(), parsed_args)
            parsed_args.actioncfg = self.get_list_action_config()
            return map(self.info_attr, self.azclass.list(parent, **vars(parsed_args)))
        except Exception as e:
            if self.verbose > 1:
                import argcomplete
                argcomplete.warn(f'argcomplete error: {e}')
            raise

    def info_attr(self, info):
        return self.azclass.info_id(info)


class AzObjectNameCompleter(AzObjectCompleter):
    def info_attr(self, info):
        return info.name


class AzObjectActionHandler(ActionHandler):
    def __call__(self, command, **opts):
        return self._handle_azobject(command.azobject, is_parent=False, **opts)

    def _handle_azobject(self, azobject, is_parent=False, **opts):
        return self.func(azobject, **opts)


class AzClassActionHandler(AzObjectActionHandler):
    def __call__(self, command, **opts):
        return self._handle_azobject(command.parent_azobject, is_parent=True, **opts)
