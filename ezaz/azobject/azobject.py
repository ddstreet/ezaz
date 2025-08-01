
import importlib
import json
import os
import subprocess

from abc import ABC
from abc import abstractmethod
from contextlib import suppress
from functools import cached_property
from itertools import chain

from ..argutil import ActionConfig
from ..argutil import ArgMap
from ..argutil import ArgUtil
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

    def __init__(self, *, verbose=False, dry_run=False, **kwargs):
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
    def azobject_cmd_arg(cls):
        return '--' + cls.azobject_name('-')

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
    def get_cmd_base(cls):
        return cls.azobject_name_list()

    @classmethod
    def is_azsubobject_container(cls):
        return False

    @classmethod
    def is_azsubobject(cls):
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

    def get_cmd_args(self, action, opts):
        return ArgMap(self.get_action_cmd_args(action, opts),
                      self.get_action_cmd_self_id_args(action, opts))

    def get_action_cmd_args(self, action, opts):
        with suppress(AttributeError):
            return getattr(self, f'get_{action}_action_cmd_args')(action, opts)
        return {}

    def get_action_cmd_self_id_args(self, action, opts):
        return {self.azobject_cmd_arg(): self.azobject_id}

    @abstractmethod
    def get_info(self, action='show', opts={}):
        pass

    @property
    def exists(self):
        try:
            self.get_info()
            return True
        except NoAzObjectExists:
            return False

    def _do_action(self, action, opts={}, *, az=None, dry_runnable=False):
        actioncfg = self.get_action_config(action)
        return (az or self.az)(*actioncfg.cmd, cmd_args=self.get_cmd_args(action, opts), dry_runnable=dry_runnable)

    def do_action(self, action, opts={}, *, az=None, dry_runnable=False):
        try:
            do_custom_action = getattr(self, f'do_{action}_action')
        except AttributeError:
            # should be able to better customize things with the actionconfig
            #actionconfig = self.get_action_configmap().get(action)
            return self._do_action(action, opts=opts, az=az, dry_runnable=dry_runnable)
        return do_custom_action(action, opts)


class AzSubObject(AzObject):
    @classmethod
    def is_azsubobject(cls):
        return True

    @classmethod
    def default_key(cls):
        return f'default_{cls.azobject_name()}'

    @classmethod
    def object_key(cls, obj_id):
        return f'{cls.azobject_name()}.{obj_id}'

    @classmethod
    def get_subcmd_args_from_parent(cls, parent, action, opts):
        return parent.get_subcmd_args(action, opts)

    def __init__(self, *, parent, azobject_id, **kwargs):
        super().__init__(**kwargs)
        self._parent = parent
        self._azobject_id = azobject_id
        assert self._parent.is_azsubobject_container()

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

    def get_parent_subcmd_args(self, action, opts):
        return self.get_subcmd_args_from_parent(self.parent, action, opts)

    def get_cmd_args(self, action, opts):
        return ArgMap(self.get_parent_subcmd_args(action, opts),
                      super().get_cmd_args(action, opts))

    def set_self_default(self, **kwargs):
        self.set_default(**{self.azobject_name(): self.azobject_id})

    def set_default(self, **kwargs):
        self.parent.set_azsubobject_default_id(self.azobject_name(),
                                               self.required_arg_value(self.azobject_name(), kwargs, 'set'))

    def clear_default(self, **kwargs):
        self.parent.del_azsubobject_default_id(self.azobject_name())


class AzSubObjectContainer(AzObject):
    @classmethod
    def azobject_subcmd_arg(cls):
        return cls.azobject_cmd_arg()

    @classmethod
    def is_azsubobject_container(cls):
        return True

    @classmethod
    @abstractmethod
    def get_azsubobject_classes(cls):
        pass

    @classmethod
    def get_azsubobject_classmap(cls):
        return {c.azobject_name(): c for c in cls.get_azsubobject_classes()}

    @classmethod
    def get_azsubobject_names(cls):
        return list(cls.get_azsubobject_classmap().keys())

    @classmethod
    def get_azsubobject_class(cls, name):
        with suppress(KeyError):
            return cls.get_azsubobject_classmap()[name]
        raise InvalidAzObjectName(f'AzObject {cls.__name__} does not contain AzObjects with name {name}')

    @classmethod
    def get_azsubobject_descendants(cls):
        return (cls.get_azsubobject_classes() +
                sum([c.get_azsubobject_descendants()
                     for c in cls.get_azsubobject_classes()
                     if c.is_azsubobject_container()], start=[]))

    def get_parent_subcmd_args(self, action, opts):
        if self.is_azsubobject():
            return super().get_parent_subcmd_args(action, opts)
        return {}

    def get_subcmd_args(self, action, opts):
        return ArgMap(self.get_parent_subcmd_args(action, opts),
                      self.get_action_subcmd_args(action, opts),
                      self.get_action_subcmd_self_id_args(action, opts))

    def get_action_subcmd_args(self, action, opts):
        with suppress(AttributeError):
            return getattr(self, f'get_{action}_action_subcmd_args')(action, opts)
        return {}

    def get_action_subcmd_self_id_args(self, action, opts):
        return {self.azobject_subcmd_arg(): self.azobject_id}

    def has_azsubobject_default_id(self, name):
        try:
            self.get_azsubobject_default_id(name)
            return True
        except DefaultConfigNotFound:
            return False

    def get_azsubobject_default_id(self, name):
        cls = self.get_azsubobject_class(name)
        try:
            return self.config[cls.default_key()]
        except KeyError:
            raise DefaultConfigNotFound(cls)

    def set_azsubobject_default_id(self, name, value):
        if self.config.get(self.get_azsubobject_class(name).default_key()) != value:
            self.config[self.get_azsubobject_class(name).default_key()] = value

    def del_azsubobject_default_id(self, name):
        with suppress(KeyError):
            del self.config[self.get_azsubobject_class(name).default_key()]

    def get_azsubobject(self, name, obj_id, info=None):
        cls = self.get_azsubobject_class(name)
        return cls(parent=self, azobject_id=obj_id, config=self.config.get_object(cls.object_key(obj_id)), info=info)

    def get_azsubobject_default(self, name):
        return self.get_azsubobject(name, self.get_azsubobject_default_id(name))

    def get_azsubobject_infos(self, name, opts={}):
        cls = self.get_azsubobject_class(name)
        actioncfg = cls.get_action_config('list')
        infos = self.az_responselist(*actioncfg.cmd, cmd_args=cls.get_subcmd_args_from_parent(self, 'list', opts))
        return self._filter_azsubobject_infos(cls, infos, opts={})

    def get_azsubobjects(self, name, opts={}):
        cls = self.get_azsubobject_class(name)
        return [self.get_azsubobject(name, cls.info_id(info), info=info) for info in
                self.get_azsubobject_infos(name, opts=opts)]

    def _filter_azsubobject_infos(self, cls, infos, opts={}):
        return [i for i in infos if self._filter_azsubobject_info(cls, i, opts=opts)]

    def _filter_azsubobject_info(self, cls, info, no_filters=False, filter_prefix=None, filter_suffix=None, filter_regex=None, opts={}):
        if self.is_azsubobject():
            if not self.parent._filter_azsubobject_info(cls, info,
                                                        no_filters=no_filters,
                                                        filter_prefix=filter_prefix,
                                                        filter_suffix=filter_suffix,
                                                        filter_regex=filter_regex,
                                                        opts=opts):
                return False
        if not QuickFilter(filter_prefix, filter_suffix, filter_regex).check(cls.info_id(info)):
            return False
        return no_filters or self.filters.check(cls.azobject_name(), cls.info_id(info))


class AzShowable(AzObject):
    @classmethod
    def get_show_action_config(cls):
        return ActionConfig('show',
                            cmd=cls.get_show_action_cmd(),
                            argconfigs=cls.get_show_action_argconfigs(),
                            description=cls.get_show_action_description())

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

    def _get_info(self, action, opts):
        return self._do_action('show', az=self.az_response, dry_runnable=True)

    def get_info(self, action='show', opts={}):
        if not self._info:
            try:
                self._info = self._get_info(action=action, opts=opts)
            except AzCommandError as aze:
                raise NoAzObjectExists(self.azobject_text(), self.azobject_id) from aze
        return self._info

    @property
    def info(self):
        # TODO - REMOVE THIS!
        return self.get_info('show', opts={})

    def do_show_action(self, action='show', opts={}):
        # TODO: move outputty-stuff from azobject...should be model ONLY. command class is view/control.
        if self.verbose:
            print(self.get_info(action, opts))
        else:
            print(self.info_id(self.get_info(action, opts)))

    def show(self):
        self.do_show_action()


class AzListable(AzSubObject):
    @classmethod
    def get_list_action_config(cls):
        return ActionConfig('list',
                            azclsmethod='do_list_action',
                            cmd=cls.get_list_action_cmd(),
                            argconfigs=cls.get_list_action_argconfigs(),
                            description=cls.get_list_action_description())

    @classmethod
    def get_list_action_cmd(cls):
        return cls.get_cmd_base() + ['list']

    @classmethod
    def get_list_action_argconfigs(cls):
        return []

    @classmethod
    def get_list_action_description(cls):
        return f'List {cls.azobject_text()}s'
 
    @classmethod
    def get_action_configmap(cls):
        return ArgMap(super().get_action_configmap(), list=cls.get_list_action_config())

    @classmethod
    def do_list_action(cls, action, *, opts={}, parent):
        for azobject in parent.get_azsubobjects(cls.azobject_name(), opts=opts):
            azobject.show()


class AzCreatable(AzObject):
    @classmethod
    def get_create_action_config(cls):
        return ActionConfig('create',
                            azobjmethod='do_create',
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

    def do_create(self, action, opts):
        if self.exists:
            raise AzObjectExists(self.azobject_text(), self.azobject_id)
        super().do_action(action=action, opts=opts)


class AzDeletable(AzObject):
    @classmethod
    def get_delete_action_config(cls):
        return ActionConfig('delete',
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


class AzRoActionable(AzShowable, AzListable):
    pass


class AzRwActionable(AzCreatable, AzDeletable):
    pass


class AzCommonActionable(AzRoActionable, AzRwActionable):
    pass
