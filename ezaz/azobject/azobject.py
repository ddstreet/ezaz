
import importlib
import json
import subprocess

from abc import ABC
from abc import abstractmethod
from collections import UserDict
from contextlib import suppress
from itertools import chain

from ..exception import AzCommandError
from ..exception import AzObjectExists
from ..exception import DefaultConfigNotFound
from ..exception import DuplicateArgument
from ..exception import NoAzObjectExists
from ..exception import NotLoggedIn
from ..exception import RequiredArgument
from ..exception import RequiredArgumentGroup
from ..response import lookup_response


class AzAction(ABC):
    @property
    @abstractmethod
    def verbose(self):
        return self.verbose

    @property
    @abstractmethod
    def dry_run(self):
        return self._dry_run

    def _trace(self, msg):
        if self.verbose:
            print(msg)

    def _expand_cmd_args(self, cmd_args):
        expanded = ([([k] + (v if isinstance(v, list) else [] if v is None else [v]))
                     for k, v in cmd_args.items()])
        return list(chain.from_iterable(expanded))

    def _exec(self, *args, cmd_args={}, check=True, dry_runnable=True, **kwargs):
        args = list(args) + self._expand_cmd_args(cmd_args)
        if self.dry_run and not dry_runnable:
            print(f'DRY-RUN (not running): {" ".join(args)}')
            return None
        self._trace(' '.join(args))
        try:
            return subprocess.run(args, check=check, **kwargs)
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


class ArgMap(UserDict):
    def __init__(self, *dicts):
        super().__init__()
        for d in dicts:
            self |= d

    def _check_dup_keys(self, other):
        dupkeys = self.keys() & other.keys()
        if dupkeys:
            k = list(dupkeys)[0]
            raise DuplicateArgument(k, self.data[k], other[k])

    def __setitem__(self, key, value):
        self._check_dup_keys({key: value})
        super().__setitem__(key, value)

    def __or__(self, other):
        self._check_dup_keys(other)
        return super().__or__(other)

    def __ror__(self, other):
        self._check_dup_keys(other)
        return super().__ror__(other)

    def __ior__(self, other):
        self._check_dup_keys(other)
        return super().__ior__(other)


class ArgUtil:
    @classmethod
    def _name_to_arg(cls, name):
        return '--' + name.replace('_', '-')

    @classmethod
    def required_arg_value(cls, arg, opts, requiring_arg=None):
        with suppress(KeyError):
            value = opts[arg]
            if value is not None:
                return value
        raise RequiredArgument(arg, requiring_arg)

    @classmethod
    def required_arg(cls, arg, opts, requiring_arg=None):
        return ArgMap({cls._name_to_arg(arg): cls.required_arg_value(arg, opts, requiring_arg)})

    @classmethod
    def required_args_one(cls, args, opts, requiring_arg=None):
        arg_group = self.optional_args(args, opts)
        if not arg_group:
            raise RequiredArgumentGroup(args, requiring_arg)
        return arg_group

    @classmethod
    def required_args_all(cls, args, opts, requiring_arg=None):
        return ArgMap(*[cls.required_arg(a, opts, requiring_arg) for a in args])

    @classmethod
    def optional_arg(cls, arg, opts):
        return cls.optional_args([arg], opts)

    @classmethod
    def optional_args(cls, args, opts):
        return ArgMap(*[{cls._name_to_arg(a): opts[a]} for a in args if a in opts])


class AzObject(AzAction, ArgUtil):
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

    def __init__(self, config, info=None):
        self._config = config
        self._info = info

    @property
    def config(self):
        return self._config

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
    def filter_parent_args(cls, opts):
        return opts

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

    def __init__(self, parent, obj_id, config, info=None):
        super().__init__(config, info=info)
        self._obj_id = obj_id
        self._parent = parent
        assert self._parent.is_azsubobject_container()

    @property
    def azobject_id(self):
        return self._obj_id

    @property
    def parent(self):
        return self._parent

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
        return cls(self, obj_id, self.config.get_object(cls.object_key(obj_id)), info=info)

    def get_azsubobjects(self, name, **kwargs):
        cls = self.get_azsubobject_class(name)
        return [self.get_azsubobject(name, cls.info_id(info), info=info) for info in
                self.az_responselist(*cls.get_cmd('list'), cmd_args=cls.get_azsubobject_cmd_args(self, 'list', kwargs))]
