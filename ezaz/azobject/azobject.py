
import importlib
import json
import os
import subprocess

from abc import ABC
from abc import abstractmethod
from contextlib import suppress
from functools import cached_property
from itertools import chain

from ..argutil import ArgUtil
from ..exception import AzCommandError
from ..exception import AzObjectExists
from ..exception import CacheExpired
from ..exception import CacheMiss
from ..exception import DefaultConfigNotFound
from ..exception import NoAzObjectExists
from ..exception import NotLoggedIn
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
    def get_base_cmd(cls):
        return cls.azobject_name_list()

    @classmethod
    def _get_cmd(cls, cmdname):
        return cmdname

    @classmethod
    def get_cmd(cls, cmdname):
        return cls.get_base_cmd() + [cls._get_cmd(cmdname)]

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

    def _get_cmd_args(self, cmdname, opts):
        return {}

    def get_cmd_args(self, cmdname, opts):
        return ArgMap({self.azobject_cmd_arg(): self.azobject_id},
                      self._get_cmd_args(cmdname, opts) or {})

    def _get_info(self):
        return self.az_response(*self.get_cmd('show'), cmd_args=self.get_cmd_args('show', {}))

    def _raise_no_az_object_exists(self, error):
        raise NoAzObjectExists(self.azobject_text(), self.azobject_id)

    def _raise_az_object_exists(self):
        raise AzObjectExists(self.azobject_text(), self.azobject_id)

    @property
    def info(self):
        if not self._info:
            try:
                self._info = self._get_info()
            except AzCommandError as aze:
                self._raise_no_az_object_exists(aze)
        return self._info

    @property
    def exists(self):
        try:
            self.info
            return True
        except NoAzObjectExists:
            return False

    def show(self):
        print(self.info if self.verbose else self.info.name)

    def create(self, **kwargs):
        if self.exists:
            self._raise_az_object_exists()
        self.az(*self.get_cmd('create'), cmd_args=self.get_cmd_args('create', kwargs), dry_runnable=False)

    def delete(self, **kwargs):
        self.az(*self.get_cmd('delete'), cmd_args=self.get_cmd_args('delete', kwargs), dry_runnable=False)


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
    def _get_azsubobject_cmd_args(cls, parent, cmdname, opts):
        return {}

    @classmethod
    def get_azsubobject_cmd_args(cls, parent, cmdname, opts):
        return ArgMap(parent.get_subcmd_args(cmdname, opts),
                      cls._get_azsubobject_cmd_args(parent, cmdname, opts) or {})

    @classmethod
    def list(cls, parent, **kwargs):
        for azobject in parent.get_azsubobjects(cls.azobject_name(), **kwargs):
            azobject.show()

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

    def get_parent_subcmd_args(self, cmdname, opts):
        return self.get_azsubobject_cmd_args(self.parent, cmdname, opts)

    def get_cmd_args(self, cmdname, opts):
        return ArgMap(self.get_parent_subcmd_args(cmdname, opts),
                      super().get_cmd_args(cmdname, opts))

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

    def get_parent_subcmd_args(self, cmdname, opts):
        if self.is_azsubobject():
            return super().get_parent_subcmd_args(cmdname, opts)
        return {}

    def _get_subcmd_args(self, cmdname, opts):
        return {}

    def get_subcmd_args(self, cmdname, opts):
        return ArgMap(self.get_parent_subcmd_args(cmdname, opts),
                      {self.azobject_subcmd_arg(): self.azobject_id},
                      self._get_subcmd_args(cmdname, opts) or {})

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

    def get_azsubobject_infos(self, name, **kwargs):
        cls = self.get_azsubobject_class(name)
        infos = self.az_responselist(*cls.get_cmd('list'), cmd_args=cls.get_azsubobject_cmd_args(self, 'list', kwargs))
        return self._filter_azsubobject_infos(cls, infos, **kwargs)

    def get_azsubobjects(self, name, **kwargs):
        cls = self.get_azsubobject_class(name)
        return [self.get_azsubobject(name, cls.info_id(info), info=info) for info in
                self.get_azsubobject_infos(name, **kwargs)]

    def _filter_azsubobject_infos(self, cls, infos, **kwargs):
        return [i for i in infos if self._filter_azsubobject_info(cls, i, **kwargs)]

    def _filter_azsubobject_info(self, cls, info, no_filters=False, filter_prefix=None, filter_suffix=None, filter_regex=None, **kwargs):
        if self.is_azsubobject():
            if not self.parent._filter_azsubobject_info(cls, info,
                                                        no_filters=no_filters,
                                                        filter_prefix=filter_prefix,
                                                        filter_suffix=filter_suffix,
                                                        filter_regex=filter_regex,
                                                        **kwargs):
                return False
        if not QuickFilter(filter_prefix, filter_suffix, filter_regex).check(cls.info_id(info)):
            return False
        return no_filters or self.filters.check(cls.azobject_name(), cls.info_id(info))
