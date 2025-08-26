
import importlib
import inspect
import json
import operator
import os
import subprocess

from abc import ABC
from abc import abstractmethod
from contextlib import contextmanager
from contextlib import suppress
from functools import cache
from functools import cached_property
from itertools import chain

from .. import AZ_TRACE_LOGGER
from .. import LOG_V0
from .. import LOG_V1
from .. import LOGGER
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
from ..exception import NullAzObject
from ..exception import RequiredArgument
from ..exception import RequiredArgumentGroup
from ..exception import UnsupportedAction
from ..filter import FILTER_ALL
from ..filter import FILTER_DEFAULT
from ..filter import Filters
from ..filter import QuickFilter
from .info import Info
from .info import info_class


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

    @property
    def _exec_environ(cls):
        return {k: v for k, v in os.environ.items() if 'ARGCOMPLETE' not in k}

    def _args_to_cmd(self, *args, cmd_args={}):
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

        for c in cmd:
            if not isinstance(c, str):
                raise RuntimeError(f'cmd value not str type: {c}')

        return cmd

    def _read_stdout_line(self, process):
        if process.stdout:
            line = process.stdout.readline()
            if self.verbose >= 2:
                AZ_TRACE_LOGGER.info(line.rstrip())
            return line
        return ''

    def _check_process(self, process, stdout, stderr):
        if process.returncode == 0:
            return

        if any(s in stderr for s in ["Please run 'az login' to setup account",
                                     "Interactive authentication is needed"]):
            raise NotLoggedIn()
        raise AzCommandError(process.args, stdout, stderr)

    def _exec(self, *args, cmd_args={}, dry_runnable=True, text=True, capture_output=False):
        cmd = self._args_to_cmd(*args, cmd_args=cmd_args)

        AZ_TRACE_LOGGER.info(' '.join(cmd))

        if self.dry_run and not dry_runnable:
            LOG_V1(f'DRY-RUN (not running): {" ".join(cmd)}')
            return ('', '')

        process = subprocess.Popen(cmd,
                                   env=self._exec_environ,
                                   text=text,
                                   stdout=subprocess.PIPE if capture_output else None,
                                   stderr=subprocess.PIPE if capture_output else None)

        stdout = ''
        while process.poll() is None:
            stdout += self._read_stdout_line(process)
        stdout += process.stdout.read() if process.stdout else ''
        stderr = process.stderr.read() if process.stderr else ''

        self._check_process(process, stdout, stderr)
        return (stdout, stderr)

    def az(self, *args, **kwargs):
        return self._exec('az', *args, **kwargs)

    def az_none(self, *args, **kwargs):
        self.az(*args, **kwargs)

    def az_stdout(self, *args, **kwargs):
        (stdout, stderr) = self.az(*args, capture_output=True, **kwargs)
        return stdout

    def az_json(self, *args, **kwargs):
        stdout = self.az_stdout(*args, **kwargs)
        return json.loads(stdout) if stdout else {}

    def az_info(self, *args, **kwargs):
        cls = info_class(args)
        j = self.az_json(*args, **kwargs)
        return cls(j, verbose=self.verbose) if j else None

    def az_infolist(self, *args, **kwargs):
        cls = info_class(args)
        j = self.az_json(*args, **kwargs)
        return cls(j, verbose=self.verbose) if j else []


class CachedAzAction(AzAction):
    def __init__(self, *, cache=None, **kwargs):
        super().__init__(**kwargs)
        self._cache = cache

    @property
    def cache(self):
        return self._cache

    def _az_cacheable_action(self, action):
        return action in ['show', 'list', 'list-locations']

    def _az_get_cache(self, cmd, action):
        if not all((self.cache, self._is_argcomplete, self._az_cacheable_action(action))):
            return None

        try:
            return self.cache.read(cmd)
        except (CacheExpired, CacheMiss, OSError):
            return None

    def _az_put_cache(self, cmd, action, stdout):
        if not all((self.cache, self._is_argcomplete, self._az_cacheable_action(action))):
            return None

        with suppress(OSError):
            self.cache.write(cmd, stdout)

    def az(self, *args, cmd_args={}, **kwargs):
        cmd = self._args_to_cmd(*args, cmd_args=cmd_args)
        action = args[-1]

        stdout = self._az_get_cache(cmd, action)
        if stdout:
            return (stdout, '')

        (stdout, stderr) = super().az(*args, cmd_args=cmd_args, **kwargs)

        self._az_put_cache(cmd, action, stdout)

        return (stdout, stderr)

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
    def get_self_id_argconfig(cls, is_parent=False, help=None, **kwargs):
        return [AzObjectArgConfig(cls.azobject_name(),
                                  cmddest=cls.get_self_id_argconfig_cmddest(is_parent=is_parent),
                                  azclass=cls,
                                  help=help or f'Use the specified {cls.azobject_text()}, instead of the default',
                                  **kwargs)]

    @classmethod
    def get_self_id_argconfig_cmddest(cls, is_parent):
        return cls.azobject_name()

    @classmethod
    def get_action_configmap(cls):
        return {}

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
    def make_action_config(cls,
                           action,
                           *,
                           aliases=None,
                           description=None,
                           argconfigs=None,
                           common_argconfigs=None,
                           az=None,
                           cmd=None,
                           pre=None,
                           post=None,
                           exception_handler=None,
                           custom_action=None,
                           custom_instance_action=None,
                           azaction_class=None,
                           **kwargs):
        if aliases is None:
            aliases = getattr(cls, f'get_{action}_action_aliases', lambda: [])()
        if description is None:
            description = getattr(cls, f'get_{action}_action_description', lambda: None)()
        if argconfigs is None:
            argconfigs = getattr(cls, f'get_{action}_action_argconfigs', lambda: None)()
        if common_argconfigs is None:
            common_argconfigs = getattr(cls, f'get_{action}_common_argconfigs', cls.get_common_argconfigs)()
        if az is None:
            az = getattr(cls, f'get_{action}_action_az', lambda: None)()
        if cmd is None:
            cmd = getattr(cls, f'get_{action}_action_cmd', lambda: cls.get_cmd_base() + [action])()
        if pre is None:
            pre = getattr(cls, f'{action}_pre', None)
        if post is None:
            post = getattr(cls, f'{action}_post', None)
        if exception_handler is None:
            exception_handler = getattr(cls, f'{action}_exception_handler', None)
        if custom_action is None:
            custom_action = getattr(cls, f'custom_{action}_action', None)
        if custom_instance_action is None:
            custom_instance_action = getattr(cls, f'custom_{action}_instance_action', None)
        if not azaction_class:
            azaction_class = AzActionConfig
        return azaction_class(action,
                              aliases=aliases,
                              description=description,
                              argconfigs=(argconfigs or []) + (common_argconfigs or []),
                              azclass=cls,
                              az=az,
                              cmd=cmd,
                              pre=pre,
                              post=post,
                              exception_handler=exception_handler,
                              custom_action=custom_action,
                              custom_instance_action=custom_instance_action,
                              **kwargs)

    @classmethod
    def get_cmd_base(cls):
        return cls.azobject_name_list()

    @classmethod
    def has_child_classes(cls):
        return False

    @classmethod
    def is_child(cls):
        return False

    @classmethod
    def info_id(cls, info):
        # Most use their 'name' as their obj_id
        return info.name

    @classmethod
    def info_cache(cls):
        if not hasattr(cls, '_info_cache'):
            cls._info_cache = {}
        return cls._info_cache

    @classmethod
    def get_instance(cls, **opts):
        if not getattr(cls, '_cached_instance', False):
            cls._cached_instance = cls(**opts)
        return cls._cached_instance

    def __init__(self, *, config, **kwargs):
        super().__init__(**kwargs)
        self._config = config

    def __str__(self):
        return str(self.info())

    def __repr__(self):
        return f'{self.__class__.__name__}(azobject_id={self.azobject_id})'

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

    def get_self_id_opts(self):
        return {self.azobject_name(): self.azobject_id}

    @abstractmethod
    def info(self):
        pass

    @property
    def exists(self):
        try:
            self.info()
            return True
        except NoAzObjectExists:
            return False


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

    @classmethod
    def get_parent_instance(cls, **opts):
        return cls.get_parent_class().get_instance(**opts)

    @classmethod
    def get_instance(cls, **opts):
        if not hasattr(cls, '_instance_cache'):
            cls._instance_cache = {}

        name = cls.azobject_name()
        azobject_id = opts.get(name)

        azobject = cls._instance_cache.get(azobject_id)
        if azobject:
            return azobject

        parent = cls.get_parent_instance(**opts)
        if not azobject_id:
            azobject_id = parent.get_default_child_id(name)

        config = parent.config.get_object(cls.object_key(azobject_id))
        cls._instance_cache[azobject_id] = cls(parent=parent, azobject_id=azobject_id, config=config)

        return cls._instance_cache[azobject_id]

    @classmethod
    def get_null_instance(cls, **opts):
        if not getattr(cls, '_null_instance', False):
            parent = cls.get_parent_class().get_instance(**opts)
            cls._null_instance = cls(parent=parent, azobject_id=None, config=None, is_null=True)
        return cls._null_instance

    def __init__(self, *, parent, azobject_id, is_null=False, **kwargs):
        super().__init__(**kwargs)
        self._parent = parent
        self._azobject_id = azobject_id
        self._is_null = is_null
        assert self._parent.has_child_classes()

    @property
    def is_null(self):
        return self._is_null

    def __repr__(self):
        if self.is_null:
            return f'{self.__class__.__name__}(null)'
        return super().__repr__()

    @property
    def exists(self):
        if self.is_null:
            return False
        return super().exists

    def get_self_id_opts(self):
        return ArgMap(**self.parent.get_self_id_opts(),
                      **super().get_self_id_opts())

    @property
    def azobject_id(self):
        if self.is_null:
            raise NullAzObject('azobject_id')
        return self._azobject_id

    @property
    def config(self):
        if self.is_null:
            raise NullAzObject('config')
        return super().config

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


class AzSubObjectContainer(AzObject):
    @classmethod
    def has_child_classes(cls):
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
                     if c.has_child_classes()], start=[]))

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

    def get_child(self, name, obj_id, info=None):
        opts = {
            self.azobject_name(): self.azobject_id,
            name: obj_id,
            'info': info,
        }
        return self.get_child_class(name).get_instance(**opts)

    def get_null_child(self, name):
        return self.get_child_class(name).get_null_instance(**{self.azobject_name(): self.azobject_id})

    def get_default_child(self, name):
        return self.get_child(name, self.get_default_child_id(name))

    def get_children(self, name, opts={}):
        null_instance = self.get_null_child(name)
        assert isinstance(null_instance, AzListable)
        return [self.get_child(name, null_instance.info_id(info), info=info)
                for info in null_instance.list(**opts)]

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
        return cls.make_action_config('show', dry_runnable=True)

    @classmethod
    def get_show_action_az(cls):
        return 'info'

    @classmethod
    def get_show_action_description(cls):
        return f'Show a {cls.azobject_text()}'
 
    @classmethod
    def get_action_configmap(cls):
        return ArgMap(super().get_action_configmap(), show=cls.get_show_action_config())

    def __init__(self, *, info=None, **kwargs):
        super().__init__(**kwargs)
        if info:
            self.info_cache().setdefault(self.azobject_id, info)

    @contextmanager
    def show_exception_handler(self):
        try:
            yield
        except AzCommandError as aze:
            raise NoAzObjectExists(self.azobject_text(), self.azobject_id) from aze

    def info(self):
        # Use the chain of our (and ancestors') azobject opts
        return self.show(**self.get_self_id_opts())

    def show_pre(self, opts):
        return self.info_cache().get(self.azobject_id)

    def show_post(self, result, opts):
        self.info_cache()[self.azobject_id] = result
        assert isinstance(result, Info)
        return result

    def show(self, **opts):
        return self.get_show_action_config().do_instance_action(self, opts)


class AzListable(AzSubObject):
    @classmethod
    def get_list_action_config(cls):
        return cls.make_action_config('list', dry_runnable=True, get_instance=cls.get_null_instance)

    @classmethod
    def get_list_action_az(cls):
        return 'infolist'

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
                if argconfig.cmddest != cls.get_self_id_argconfig_cmddest(is_parent=is_parent)]

    @classmethod
    def get_list_action_description(cls):
        return f'List {cls.azobject_text()}s'
 
    @classmethod
    def get_action_configmap(cls):
        return ArgMap(super().get_action_configmap(), list=cls.get_list_action_config())

    def list_pre(self, opts):
        if getattr(self.__class__, '_info_cache_complete', False):
            return self.list_post(self.info_cache().values(), opts)
        return None

    def list_post(self, result, opts):
        if not getattr(self.__class__, '_info_cache_complete', False):
            for info in result:
                assert isinstance(info, Info)
                self.info_cache()[self.info_id(info)] = info
            self.__class__._info_cache_complete = True

        return [info for info in result
                if self.parent.filter_azobject_id(self.azobject_name(),
                                                  self.info_id(info),
                                                  prefix=opts.get('filter_prefix'),
                                                  suffix=opts.get('filter_suffix'),
                                                  regex=opts.get('filter_regex'),
                                                  no_filters=opts.get('no_filters'))]

    def list(self, **opts):
        return self.get_list_action_config().do_instance_action(self, opts)


class AzCreatable(AzObject):
    @classmethod
    def get_create_action_config(cls):
        return cls.make_action_config('create')

    @classmethod
    def get_create_action_az(cls):
        return 'info'

    @classmethod
    def get_create_action_description(cls):
        return f'Create a {cls.azobject_text()}'

    @classmethod
    def get_action_configmap(cls):
        return ArgMap(super().get_action_configmap(), create=cls.get_create_action_config())

    def create_pre(self, opts):
        if self.exists:
            raise AzObjectExists(self.azobject_text(), self.azobject_id)
        return None

    def create(self, **opts):
        return self.get_create_action_config().do_instance_action(self, opts)


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

    def delete_pre(self, opts):
        if not self.exists:
            raise NoAzObjectExists(self.azobject_text(), self.azobject_id)
        return None

    def delete(self, **opts):
        self.get_delete_action_config().do_instance_action(self, opts)


# Do not ever actually call the show command, always use the list
# command.  This is appropriate for classes that don't support show,
# or have a quick list response.  This should not be used for classes
# where list is slow.
class AzEmulateShowable(AzShowable, AzListable):
    def show_pre(self, opts):
        self.list(**opts)
        with suppress(KeyError):
            return self.info_cache()[self.azobject_id]
        raise NoAzObjectExists(self.azobject_text(), self.azobject_id)


class AzRoActionable(AzShowable, AzListable):
    pass


class AzRwActionable(AzCreatable, AzDeletable):
    pass


class AzCommonActionable(AzRoActionable, AzRwActionable):
    pass


class AzActionConfig(ActionConfig):
    def __init__(self,
                 action,
                 *,
                 azclass=None,
                 get_instance=None,
                 cmd=None,
                 az=None,
                 dry_runnable=False,
                 parse_opts=None,
                 pre=None,
                 instance_opts=None,
                 post=None,
                 exception_handler=None,
                 custom_action=None,
                 custom_instance_action=None,
                 **kwargs):
        super().__init__(action, **kwargs)
        self.azclass = azclass
        self.get_instance = get_instance or azclass.get_instance
        self.cmd = cmd or azclass.get_cmd_base() + [action]
        self.az = az or 'none'
        self.dry_runnable = dry_runnable
        self.pre = pre or self._noop_pre
        self.post = post or self._noop_post
        self.exception_handler = exception_handler or self._noop_exception_handler
        self.custom_action = custom_action
        self.custom_instance_action = custom_instance_action

    def _noop_pre(self, azobject, opts):
        return None

    def _noop_post(self, azobject, result, opts):
        return result

    @contextmanager
    def _noop_exception_handler(self, *args):
        yield

    def do_action(self, **opts):
        if self.custom_action:
            result = self.custom_action(self, opts)
        else:
            result = self._do_action(**opts)
        if isinstance(result, list):
            for r in result:
                LOG_V0(r)
        elif result:
            LOG_V0(result)

    def _do_action(self, **opts):
        if self.is_action('create') or self.is_action('delete'):
            if not opts.get(self.azclass.azobject_name()):
                raise RequiredArgument(self.azclass.azobject_name(), self.action)

        return self.do_instance_action(self.get_instance(**opts), opts)

    def do_instance_action(self, azobject, opts):
        if self.custom_instance_action:
            return self.custom_instance_action(self, azobject, opts)
        return self._do_instance_action(azobject, opts)

    def _do_instance_action(self, azobject, opts):
        result = self.pre(azobject, opts)
        if result:
            return result

        az = getattr(azobject, f'az_{self.az}')

        with self.exception_handler(azobject):
            return self.post(azobject, az(*self.cmd, cmd_args=self.cmd_args(**opts), dry_runnable=self.dry_runnable), opts)
