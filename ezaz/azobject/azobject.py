
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

from .. import AZ_LOGGER
from .. import LOGGER
from ..actionutil import ActionConfig
from ..argutil import ArgConfig
from ..argutil import ArgMap
from ..argutil import ArgUtil
from ..argutil import AzObjectArgConfig
from ..argutil import BoolArgConfig
from ..argutil import GroupArgConfig
from ..cache import Cache
from ..config import Config
from ..exception import AzCommandError
from ..exception import AzObjectExists
from ..exception import CacheError
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
from ..filter import Filter
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
            AZ_LOGGER.debug(line.rstrip())
            return line
        return ''

    def _check_process(self, process, stdout, stderr):
        if process.returncode == 0:
            return

        if any(s in stderr for s in ["Please run 'az login' to setup account",
                                     "Interactive authentication is needed",
                                     "InteractionRequired"]):
            raise NotLoggedIn()
        raise AzCommandError(process.args, stdout, stderr)

    def _exec(self, *args, cmd_args={}, dry_runnable=True, text=True, capture_output=False):
        cmd = self._args_to_cmd(*args, cmd_args=cmd_args)

        AZ_LOGGER.info(' '.join(cmd))

        if self.dry_run and not dry_runnable:
            LOGGER.warning(f'DRY-RUN (not running): {" ".join(cmd)}')
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


class AzObject(AzAction):
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
    def azobject_key(cls, azobject_id):
        return f'{cls.azobject_name()}.{azobject_id}'

    @classmethod
    def get_aliases(cls):
        return []

    @classmethod
    def get_description(cls):
        return None

    @classmethod
    def get_argconfigs(cls):
        return []

    @classmethod
    def get_argconfigs_title(cls):
        return None

    @classmethod
    def get_common_argconfigs(cls, is_parent=False):
        return []

    @classmethod
    def get_common_argconfigs_title(cls):
        return None

    @classmethod
    def get_self_id_argconfigs(cls, *args, is_parent=False, **kwargs):
        if 'help' not in kwargs:
            kwargs['help'] = 'Use the specified {azobject_text}, instead of the default'
        if kwargs['help']:
            kwargs['help'] = kwargs['help'].format(azobject_name=cls.azobject_name(),
                                                   azobject_text=cls.azobject_text())
        if 'cmddest' not in kwargs:
            kwargs['cmddest'] = cls.get_self_id_argconfig_cmddest(is_parent=is_parent)
        if 'metavar' not in kwargs:
            kwargs['metavar'] = cls.azobject_name().upper()
        return [AzObjectArgConfig(*args, azclass=cls, **kwargs)]

    @classmethod
    def get_self_id_argconfig_cmddest(cls, is_parent):
        return cls.azobject_name()

    @classmethod
    def get_azobject_id_argconfigs(cls, is_parent=False, **kwargs):
        return cls.get_self_id_argconfigs(is_parent=is_parent, **kwargs)

    @classmethod
    def get_azobject_id_argconfigs_title(cls):
        return 'Resource options'

    @classmethod
    def get_action_configs(cls):
        return []

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
                           argconfigs_title=None,
                           common_argconfigs=None,
                           common_argconfigs_title=None,
                           azobject_id_argconfigs=None,
                           azobject_id_argconfigs_title=None,
                           az=None,
                           cmd=None,
                           pre=None,
                           post=None,
                           context_manager=None,
                           get_instance=None,
                           handler=None,
                           instance_handler=None,
                           dry_runnable=None,
                           azaction_class=None,
                           **kwargs):
        if aliases is None:
            aliases = getattr(cls, f'get_{action}_action_aliases', cls.get_aliases)()
        if description is None:
            description = getattr(cls, f'get_{action}_action_description', cls.get_description)()
        if argconfigs is None:
            argconfigs = getattr(cls, f'get_{action}_action_argconfigs', cls.get_argconfigs)()
        if argconfigs_title is None:
            argconfigs_title = getattr(cls, f'get_{action}_action_argconfigs_title', cls.get_argconfigs_title)()
        if argconfigs_title:
            argconfigs = [GroupArgConfig(*argconfigs, title=argconfigs_title)]
        if common_argconfigs is None:
            common_argconfigs = getattr(cls, f'get_{action}_action_common_argconfigs', cls.get_common_argconfigs)()
        if common_argconfigs_title is None:
            common_argconfigs_title = getattr(cls, f'get_{action}_action_common_argconfigs_title', cls.get_common_argconfigs_title)()
        if common_argconfigs_title:
            common_argconfigs = [GroupArgConfig(*common_argconfigs, title=common_argconfigs_title)]
        if azobject_id_argconfigs is None:
            azobject_id_argconfigs = getattr(cls, f'get_{action}_action_azobject_id_argconfigs', cls.get_azobject_id_argconfigs)()
        if azobject_id_argconfigs_title is None:
            azobject_id_argconfigs_title = getattr(cls, f'get_{action}_action_azobject_id_argconfigs_title', cls.get_azobject_id_argconfigs_title)()
        if azobject_id_argconfigs_title:
            azobject_id_argconfigs = [GroupArgConfig(*azobject_id_argconfigs, title=azobject_id_argconfigs_title)]
        if get_instance is None:
            get_instance = getattr(cls, f'get_{action}_action_get_instance', lambda: None)()
        if dry_runnable is None:
            dry_runnable = getattr(cls, f'get_{action}_action_dry_runnable', lambda: False)()
        if az is None:
            az = getattr(cls, f'get_{action}_action_az', lambda: None)()
        if cmd is None:
            cmd = getattr(cls, f'get_{action}_action_cmd', lambda: None)()
        if pre is None:
            pre = getattr(cls, f'{action}_pre', None)
        if post is None:
            post = getattr(cls, f'{action}_post', None)
        if context_manager is None:
            context_manager = getattr(cls, f'{action}_context_manager', None)
        if handler is None:
            handler = getattr(cls, f'{action}_handler', None)
        if instance_handler is None:
            instance_handler = getattr(cls, f'{action}_instance_handler', None)
        if not azaction_class:
            azaction_class = AzActionConfig
        return azaction_class(action,
                              aliases=aliases,
                              description=description,
                              argconfigs=[*argconfigs, *common_argconfigs, *azobject_id_argconfigs],
                              azclass=cls,
                              az=az,
                              cmd=cmd,
                              pre=pre,
                              post=post,
                              context_manager=context_manager,
                              get_instance=get_instance,
                              handler=handler,
                              instance_handler=instance_handler,
                              dry_runnable=dry_runnable,
                              **kwargs)

    @classmethod
    def get_cmd_base(cls):
        return cls.azobject_name_list()

    @classmethod
    def has_child_classes(cls):
        return False

    @classmethod
    def has_parent_class(cls):
        return False

    @classmethod
    def get_azobject_id_from_opts(cls, opts, required=False):
        azobject_id = opts.get(cls.azobject_name())
        if not azobject_id and required:
            raise RequiredArgument(cls.azobject_name(),
                                   required_by=required if isinstance(required, str) else None)
        return azobject_id

    @classmethod
    def set_azobject_id_in_opts(cls, azobject_id, opts, replace=True):
        if replace or cls.get_azobject_id_from_opts(opts) is None:
            opts[cls.azobject_name()] = azobject_id
        return opts

    @classmethod
    @abstractmethod
    def get_default_azobject_id(cls, **opts):
        pass

    @classmethod
    @abstractmethod
    def set_default_azobject_id(cls, azobject_id):
        pass

    @classmethod
    @abstractmethod
    def del_default_azobject_id(cls):
        pass

    @classmethod
    def get_instance(cls, **opts):
        with suppress(RequiredArgument):
            return cls.get_specific_instance(**opts)
        return cls.get_default_instance(**opts)

    @classmethod
    def get_default_instance(cls, **opts):
        default_id = cls.get_default_azobject_id(**opts)
        return cls.get_specific_instance(**cls.set_azobject_id_in_opts(default_id, opts))

    @classmethod
    def get_specific_instance(cls, **opts):
        instance_cache = cls.instance_cache(**opts)

        azobject_id = cls.get_azobject_id_from_opts(opts, required=True)
        if azobject_id:
            azobject = instance_cache.get(azobject_id)
            if azobject:
                return azobject

        instance_cache[azobject_id] = cls._get_specific_instance(azobject_id, opts)
        return instance_cache[azobject_id]

    @classmethod
    @abstractmethod
    def instance_cache(cls, **opts):
        pass

    @classmethod
    @abstractmethod
    def _get_specific_instance(cls, azobject_id, opts):
        pass

    @classmethod
    def get_null_instance(cls, **opts):
        instance_cache = cls.instance_cache(**opts)
        if not instance_cache.get(None):
            instance_cache[None] = cls._get_null_instance(**opts)
        return instance_cache[None]

    @classmethod
    def _get_null_instance(cls, **opts):
        return cls(azobject_id=None, is_null=True, **opts)

    @classmethod
    def has_filter(cls):
        return False

    def __init__(self, *, azobject_id, cachedir=None, configfile=None, is_null=False, **kwargs):
        super().__init__(**kwargs)
        self._cachedir = cachedir
        self._configfile = configfile
        self._azobject_id = azobject_id
        self.is_null = is_null
        assert azobject_id or is_null

    def __str__(self):
        with suppress(NoAzObjectExists, NullAzObject):
            return str(self.info())
        return self.__repr__()

    def __repr__(self):
        with suppress(NullAzObject):
            return f'{self.__class__.__name__}(azobject_id={self.azobject_id})'
        return f'{self.__class__.__name__}(null)'

    @property
    def _cache(self):
        if not getattr(self.__class__, '_class_cache', None):
            self.__class__._class_cache = Cache(cachepath=self._cachedir, verbose=self.verbose, dry_run=self.dry_run)
        return self.__class__._class_cache

    @cached_property
    def cache(self):
        if self.is_null:
            return self._cache.class_cache(self.azobject_name())
        return self._cache.object_cache(self.azobject_name(), self.azobject_id)

    @cached_property
    def config(self):
        if self.is_null:
            raise NullAzObject('config')
        return Config(self._configfile).get_object(self.azobject_key(self.azobject_id))

    @property
    def azobject_id(self):
        if self.is_null:
            raise NullAzObject('azobject_id')
        return self._azobject_id

    def get_azobject_id_opts(self, **opts):
        if not self.is_null:
            return self.set_azobject_id_in_opts(self.azobject_id, opts, replace=False)
        return opts

    def do_action_config_instance_action(self, action, opts, include_self=True):
        if include_self:
            opts = self.get_azobject_id_opts(**opts)
        return self.get_action_config(action).do_instance_action(self, opts)

    @abstractmethod
    def info(self):
        pass

    @property
    def is_default(self):
        with suppress(DefaultConfigNotFound, NullAzOnbject):
            return self.get_default_azobject_id(self.get_azobject_id_opts()) == self.azobject_id
        return False

    @property
    def exists(self):
        with suppress(NoAzObjectExists, NullAzObject):
            self.info()
            return True
        return False


class AzSubObject(AzObject):
    @classmethod
    def has_parent_class(cls):
        return True

    @classmethod
    @abstractmethod
    def get_parent_class(cls):
        pass

    @classmethod
    def get_parent_ancestor_classes(cls):
        return (cls.get_parent_class().get_ancestor_classes()
                if cls.get_parent_class().has_parent_class()
                else [])

    @classmethod
    def get_ancestor_classes(cls):
        return [*cls.get_parent_ancestor_classes(), cls.get_parent_class()]

    @classmethod
    def get_parent_common_argconfigs(cls):
        return cls.get_parent_class().get_common_argconfigs(is_parent=True)

    @classmethod
    def get_common_argconfigs(cls, is_parent=False):
        return [*cls.get_parent_common_argconfigs(),
                *super().get_common_argconfigs(is_parent=is_parent)]

    @classmethod
    def get_parent_azobject_id_argconfigs(cls, **kwargs):
        return cls.get_parent_class().get_azobject_id_argconfigs(is_parent=True, **kwargs)

    @classmethod
    def get_azobject_id_argconfigs(cls, is_parent=False, **kwargs):
        return [*cls.get_parent_azobject_id_argconfigs(**kwargs),
                *super().get_azobject_id_argconfigs(is_parent=is_parent, **kwargs)]

    @classmethod
    def get_parent_instance(cls, **opts):
        return cls.get_parent_class().get_instance(**opts)

    @classmethod
    def instance_cache(cls, **opts):
        return cls.get_parent_instance(**opts).get_child_instance_cache(cls)

    @classmethod
    def _get_specific_instance(cls, azobject_id, opts):
        return cls(parent=cls.get_parent_instance(**opts), azobject_id=azobject_id, **opts)

    @classmethod
    def _get_null_instance(cls, **opts):
        return super()._get_null_instance(parent=cls.get_parent_instance(**opts), **opts)

    @classmethod
    def default_key(cls):
        return f'default_{cls.azobject_name()}'

    @classmethod
    def get_default_azobject_id(cls, **opts):
        return cls.get_parent_instance(**opts).get_default_child_id(cls.azobject_name())

    @classmethod
    def set_default_azobject_id(cls, azobject_id, opts):
        cls.get_parent_instance(**opts).set_default_child_id(cls.azobject_name(), azobject_id)

    @classmethod
    def del_default_azobject_id(cls, **opts):
        cls.get_parent_instance(**opts).del_default_child_id(cls.azobject_name())

    @classmethod
    def filter_key(cls):
        return f'filter_{cls.azobject_name()}'

    @classmethod
    def has_filter(cls):
        return True

    @classmethod
    def get_filter(cls, **opts):
        return cls.get_parent_instance(**opts).get_child_filter(cls.azobject_name())

    @classmethod
    def set_filter(cls, new_filter, opts):
        cls.get_parent_instance(**opts).set_child_filter(cls.azobject_name(), new_filter)

    @classmethod
    def del_filter(cls, **opts):
        cls.get_parent_instance(**opts).del_child_filter(cls.azobject_name())

    @classmethod
    def filter_infos(cls, infos, opts):
        f = cls.get_filter(**opts)
        for info in infos:
            if f.check_info(info):
                yield info

    def __init__(self, *, parent, **kwargs):
        super().__init__(**kwargs)
        self._parent = parent
        assert self.parent.has_child_classes()

    def get_azobject_id_opts(self, **opts):
        return super().get_azobject_id_opts(**self.parent.get_azobject_id_opts(**opts))

    @property
    def parent(self):
        return self._parent

    @cached_property
    def cache(self):
        if self.is_null:
            return self.parent.cache.child_class_cache(self.azobject_name())
        return self.parent.cache.child_object_cache(self.azobject_name(), self.azobject_id)

    @cached_property
    def config(self):
        return self.parent.config.get_object(self.azobject_key(self.azobject_id))

    @property
    def verbose(self):
        return self.parent.verbose

    @property
    def dry_run(self):
        return self.parent.dry_run


class AzObjectContainer(AzObject):
    @classmethod
    def has_child_classes(cls):
        return True

    @classmethod
    @abstractmethod
    def get_child_classes(cls):
        pass

    @classmethod
    def get_child_class(cls, name):
        for c in cls.get_child_classes():
            if c.azobject_name() == name:
                return c
        raise InvalidAzObjectName(f'AzObject {cls.__name__} does not contain AzObjects with name {name}')

    @classmethod
    def get_descendant_classes(cls):
        return sum([c.get_descendant_classes() for c in cls.get_child_classes() if c.has_child_classes()],
                   start=cls.get_child_classes())

    @classmethod
    def get_descendant_azobject_id_argconfigs(cls, include_self=False, is_parent=True, **kwargs):
        return sum([c.get_self_id_argconfigs(is_parent=is_parent, **kwargs)
                    for c in cls.get_descendant_classes()],
                   start=cls.get_self_id_argconfigs(is_parent=is_parent, **kwargs) if include_self else [])

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
        self.config[self.get_child_class(name).default_key()] = value

    def del_default_child_id(self, name):
        with suppress(KeyError):
            del self.config[self.get_child_class(name).default_key()]

    def get_specific_child(self, name, opts={}):
        obj_id = opts.get(name)
        if not obj_id:
            return None
        return self.get_child(name, obj_id)

    @cache
    def get_child_instance_cache(self, cls):
        return {}

    def get_child(self, name, obj_id, info=None):
        return self.get_child_class(name).get_instance(**self.get_azobject_id_opts(**{name: obj_id, 'info': info}))

    def get_null_child(self, name):
        return self.get_child_class(name).get_null_instance(**self.get_azobject_id_opts())

    def get_default_child(self, name):
        return self.get_child(name, self.get_default_child_id(name))

    def get_children(self, name, opts={}):
        null_instance = self.get_null_child(name)
        assert isinstance(null_instance, AzListable)
        return [self.get_child(name, info._id, info=info)
                for info in null_instance.list(no_filters=True, **opts)]

    def get_child_filter(self, name):
        return Filter(self.config.get_object(self.get_child_class(name).filter_key()))

    def set_child_filter(self, name, value):
        self.config[self.get_child_class(name).filter_key()] = Filter(value).config

    def del_child_filter(self, name):
        with suppress(KeyError):
            del self.config[self.get_child_class(name).filter_key()]


class AzSubObjectContainer(AzObjectContainer, AzSubObject):
    pass


class AzShowable(AzObject):
    @classmethod
    def get_action_configs(cls):
        return [*super().get_action_configs(), cls.get_show_action_config()]

    @classmethod
    def get_show_action_config(cls):
        return cls.make_action_config('show')

    @classmethod
    def get_show_action_dry_runnable(cls):
        return True

    @classmethod
    def get_show_action_az(cls):
        return 'info'

    @classmethod
    def get_show_action_description(cls):
        return f'Show a {cls.azobject_text()}'

    def __init__(self, *, info=None, **kwargs):
        super().__init__(**kwargs)
        if info:
            self.cache.write_info(info=info)

    @contextmanager
    def show_context_manager(self):
        try:
            yield
        except AzCommandError as aze:
            raise NoAzObjectExists(self.azobject_text(), self.azobject_id) from aze

    def info(self):
        return self.show()

    def show_pre(self, opts):
        with suppress(CacheError):
            return self.cache.read_info()
        return None

    def show(self, **opts):
        return self.do_action_config_instance_action('show', opts)

    def show_post(self, result, opts):
        self.cache.write_info(info=result)
        return result


class AzListable(AzObject):
    @classmethod
    def get_action_configs(cls):
        return [*super().get_action_configs(), cls.get_list_action_config()]

    @classmethod
    def get_list_action_config(cls):
        return cls.make_action_config('list')

    @classmethod
    def get_list_action_dry_runnable(cls):
        return True

    @classmethod
    def get_list_action_az(cls):
        return 'infolist'

    @classmethod
    def get_list_action_get_instance(cls):
        return cls.get_null_instance

    @classmethod
    def get_list_action_argconfigs(cls):
        return [GroupArgConfig(ArgConfig('prefix', noncmd=True, help=f'List only {cls.azobject_text()}s that start with the prefix'),
                               ArgConfig('suffix', noncmd=True, help=f'List only {cls.azobject_text()}s that end with the suffix'),
                               ArgConfig('regex', noncmd=True, help=f'List only {cls.azobject_text()}s that match the regular expression'),
                               BoolArgConfig('-N', '--no-filters', noncmd=True, help=f'Do not use any configured filters (only use the CLI parameters)'),
                               title='Filter options')]

    @classmethod
    def get_list_action_azobject_id_argconfigs(cls):
        # Don't include our self id param for list action
        return [argconfig for argconfig in cls.get_azobject_id_argconfigs()
                if argconfig.cmddest != cls.get_self_id_argconfig_cmddest(is_parent=False)]

    @classmethod
    def get_list_action_description(cls):
        return f'List {cls.azobject_text()}s'

    def _list_filter(self, infos, opts):
        infos = [info for info in infos if Filter(opts).check_info(info)]
        if opts.get('no_filters') or not self.has_filter():
            return infos
        else:
            return self.filter_infos(infos, opts)

    def list_pre(self, opts):
        with suppress(CacheError):
            return self.cache.read_info_list()
        return None

    def list(self, **opts):
        return self.do_action_config_instance_action('list', opts)

    def list_post(self, result, opts):
        self.cache.write_info_list(infolist=result)
        return list(self._list_filter(result, opts))


class AzCreatable(AzObject):
    @classmethod
    def get_action_configs(cls):
        return [*super().get_action_configs(), cls.get_create_action_config()]

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
    def get_create_action_argconfigs_title(cls):
        return f'{cls.azobject_text().capitalize()} creation options'

    @classmethod
    def get_create_action_azobject_id_argconfigs(cls):
        return cls.get_azobject_id_argconfigs()

    @classmethod
    def is_create_id_required(self):
        # Do we require the id to be specified for create operation?
        return True

    def create_pre(self, opts):
        if self.is_create_id_required():
            self.get_azobject_id_from_opts(opts, required='create')
        if self.exists:
            raise AzObjectExists(self.azobject_text(), self.azobject_id)
        return None

    def create(self, **opts):
        return self.do_action_config_instance_action('create', opts, include_self=False)


class AzDeletable(AzObject):
    @classmethod
    def get_action_configs(cls):
        return [*super().get_action_configs(), cls.get_delete_action_config()]

    @classmethod
    def get_delete_action_config(cls):
        return cls.make_action_config('delete')

    @classmethod
    def get_delete_action_description(cls):
        return f'Delete a {cls.azobject_text()}'

    @classmethod
    def get_delete_action_argconfigs_title(cls):
        return f'{cls.azobject_text().capitalize()} deletion options'

    @classmethod
    def get_delete_action_azobject_id_argconfigs(cls):
        return cls.get_azobject_id_argconfigs()

    @classmethod
    def is_create_id_required(self):
        # Do we require the id to be specified for delete operation?
        return True

    def delete_pre(self, opts):
        if self.is_create_id_required():
            self.get_azobject_id_from_opts(opts, required='delete')
        if not self.exists:
            raise NoAzObjectExists(self.azobject_text(), self.azobject_id)
        return None

    def delete(self, **opts):
        return self.do_action_config_instance_action('delete', opts, include_self=False)


# Do not ever actually call the show command, always use the list
# command.  This is appropriate for classes that don't support show,
# or have a quick list response.  This should not be used for classes
# where list is slow.
class AzEmulateShowable(AzShowable, AzListable):
    def show_pre(self, opts):
        self.list(**opts)
        with suppress(CacheError):
            return self.cache.read_info()
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
                 context_manager=None,
                 handler=None,
                 instance_handler=None,
                 **kwargs):
        super().__init__(action, **kwargs)
        self.azclass = azclass
        self.get_instance = get_instance or azclass.get_instance
        self.cmd = cmd or azclass.get_cmd_base() + [action]
        self.az = az or 'none'
        self.dry_runnable = dry_runnable
        self.pre = pre or self._noop_pre
        self.post = post or self._noop_post
        self.context_manager = context_manager or self._noop_context_manager
        self.handler = handler
        self.instance_handler = instance_handler

    def _noop_pre(self, azobject, opts):
        return None

    def _noop_post(self, azobject, result, opts):
        return result

    @contextmanager
    def _noop_context_manager(self, *args):
        yield

    def do_action(self, **opts):
        if self.handler:
            result = self.handler(self, opts)
        else:
            result = self._do_action(**opts)
        if isinstance(result, list):
            for r in result:
                print(r)
        elif result:
            print(result)

    def _do_action(self, **opts):
        return self.do_instance_action(self.get_instance(**opts), opts)

    def do_instance_action(self, azobject, opts):
        if self.instance_handler:
            return self.instance_handler(self, azobject, opts)
        return self._do_instance_action(azobject, opts)

    def _do_instance_action(self, azobject, opts):
        result = self.pre(azobject, opts)
        if result is not None:
            return result

        az = getattr(azobject, f'az_{self.az}')

        with self.context_manager(azobject):
            return self.post(azobject, az(*self.cmd, cmd_args=self.cmd_args(**opts), dry_runnable=self.dry_runnable), opts)
