
import importlib
import json
import subprocess

from abc import ABC
from abc import abstractmethod
from collections import ChainMap
from contextlib import suppress
from functools import partial
from functools import partialmethod
from itertools import chain

from ..exception import NotLoggedIn
from ..exception import RequiredArgument
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

    def required_arg(self, arg, _requiring_arg=None, **kwargs):
        try:
            return kwargs[arg]
        except KeyError:
            raise RequiredArgument(arg, _requiring_arg)

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
        return subprocess.run(args, check=check, **kwargs)

    def az(self, *args, capture_output=False, **kwargs):
        return self._exec('az', *args, capture_output=capture_output, **kwargs)

    def az_stdout(self, *args, **kwargs):
        try:
            cp = self.az(*args, capture_output=True, text=True, **kwargs)
        except subprocess.CalledProcessError as cpe:
            if any(s in cpe.stderr for s in ["Please run 'az login' to setup account",
                                             "Interactive authentication is needed"]):
                raise NotLoggedIn()
            raise
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


class AzObject(AzAction):
    @classmethod
    def info_id(cls, info):
        # Most use their 'name' as their obj_id
        return info.name

    @classmethod
    @abstractmethod
    def get_base_cmd(cls):
        pass

    @classmethod
    def get_show_cmd(cls):
        return cls.get_base_cmd() + ['show']

    @classmethod
    def get_create_cmd(cls):
        return cls.get_base_cmd() + ['create']

    @classmethod
    def get_delete_cmd(cls):
        return cls.get_base_cmd() + ['delete']

    def __init__(self, config, info=None):
        self._config = config
        self._info = info

    @property
    def config(self):
        return self._config

    def get_cmd_args(self, opts):
        return {}

    def get_show_cmd_args(self, opts):
        return self.get_cmd_args(opts)

    def get_create_cmd_args(self, opts):
        return self.get_cmd_args(opts)

    def get_delete_cmd_args(self, opts):
        return self.get_cmd_args(opts)

    def _merge_cmd_args(self, a, b):
        dup_keys = list(a.keys() & b.keys())
        if dup_keys:
            k = dup_keys[0]
            raise DuplicateArgument(k, a[k], b[k])
        return a | b

    def _get_info(self):
        return self.az_response(*self.get_show_cmd(), cmd_args=self.get_show_cmd_args({}))

    @property
    def info(self):
        if not self._info:
            self._info = self._get_info()
        return self._info

    def show(self):
        if self.verbose and hasattr(self.info, 'id'):
            print(f'{self.info.name} (id: {self.info.id})')
        else:
            print(self.info.name)

    def create(self, **kwargs):
        self.az(*self.get_create_cmd(), cmd_args=self.get_create_cmd_args(kwargs), dry_runnable=False)

    def delete(self, **kwargs):
        self.az(*self.get_delete_cmd(), cmd_args=self.get_delete_cmd_args(kwargs), dry_runnable=False)


class AzSubObject(AzObject):
    @classmethod
    @abstractmethod
    def subobject_name_list(cls):
        pass

    @classmethod
    def subobject_name(cls, sep='_'):
        return sep.join(cls.subobject_name_list())

    @classmethod
    def get_base_cmd(cls):
        return cls.subobject_name_list()

    @classmethod
    def default_key(cls):
        return f'default_{cls.subobject_name()}'

    @classmethod
    def object_key(cls, obj_id):
        return f'{cls.subobject_name()}.{obj_id}'

    @classmethod
    def get_list_cmd(cls):
        return cls.get_base_cmd() + ['list']

    @classmethod
    def filter_parent_args(cls, *args):
        return args

    def __init__(self, parent, obj_id, config, info=None):
        super().__init__(config, info=info)
        self._obj_id = obj_id
        self._parent = parent
        assert isinstance(self._parent, AzSubObjectContainer)

    @property
    def object_id(self):
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

    def get_parent_subcmd_args(self, opts):
        return self.parent.get_subcmd_args(opts)

    def get_my_cmd_args(self, opts):
        return {}

    def get_my_show_cmd_args(self, opts):
        return self.get_my_cmd_args(opts)

    def get_my_create_cmd_args(self, opts):
        return self.get_my_cmd_args(opts)

    def get_my_delete_cmd_args(self, opts):
        return self.get_my_cmd_args(opts)

    def get_cmd_args(self, opts):
        return self._merge_cmd_args(self.get_parent_subcmd_args(opts),
                                    self.get_my_cmd_args(opts))

    def get_show_cmd_args(self, opts):
        return self._merge_cmd_args(self.get_parent_subcmd_args(opts),
                                    self.get_my_show_cmd_args(opts))

    def get_create_cmd_args(self, opts):
        return self._merge_cmd_args(self.get_parent_subcmd_args(opts),
                                    self.get_my_create_cmd_args(opts))

    def get_delete_cmd_args(self, opts):
        return self._merge_cmd_args(self.get_parent_subcmd_args(opts),
                                    self.get_my_delete_cmd_args(opts))


class AzSubObjectContainer(AzObject):
    def get_parent_subcmd_args(self, opts):
        if isinstance(self, AzSubObject):
            return super().get_parent_subcmd_args(opts)
        return {}

    def get_my_subcmd_args(self, opts):
        if isinstance(self, AzSubObject):
            return self.get_my_cmd_args(opts)
        return self.get_cmd_args(opts)

    def get_subcmd_args(self, opts):
        return self._merge_cmd_args(self.get_parent_subcmd_args(opts),
                                    self.get_my_subcmd_args(opts))

    def get_list_cmd_args(self, cls, opts):
        return cls.filter_parent_args(self.get_subcmd_args(opts))

    # TODO - rework this to directly call classmethod cls.list()
    def list(self, cls, **kwargs):
        return self.az_responselist(*cls.get_list_cmd(), cmd_args=self.get_list_cmd_args(cls, kwargs))

    def get_default_azobject_id(self, cls):
        try:
            return self.config[cls.default_key()]
        except KeyError:
            not_found = getattr(importlib.import_module('..exception', __name__),
                                f'{cls.__name__}DefaultConfigNotFound')
            raise not_found()

    def set_default_azobject_id(self, cls, value):
        if self.config.get(cls.default_key()) != value:
            self.config[cls.default_key()] = value

    def del_default_azobject_id(self, cls):
        with suppress(KeyError):
            del self.config[cls.default_key()]

    def get_azobject(self, cls, obj_id, info=None):
        return cls(self, obj_id, self.config.get_object(cls.object_key(obj_id)), info=info)

    def get_default_azobject(self, cls):
        return getattr(self, f'get_{cls.subobject_name()}')(getattr(self, cls.default_key()))

    def get_azobjects(self, cls, **kwargs):
        return [getattr(self, f'get_{cls.subobject_name()}')(cls.info_id(info), info=info)
                for info in self.list(cls, **kwargs)]


# TODO - remove this and just call the generic methods from command classes
def AzSubObjectContainerChildren(children=[]):
    containerclasses = []

    for cls in children:
        assert issubclass(cls, AzSubObject)

        containerclasses.append(type(f'{cls.__name__}Container',
                                     (),
                                     {cls.default_key(): property(fget=lambda self: self.get_default_azobject_id(cls),
                                                                  fset=lambda self, value: self.set_default_azobject_id(cls, value),
                                                                  fdel=lambda self: self.del_default_azobject_id(cls)),
                                      f'get_{cls.subobject_name()}': lambda self, obj_id, info=None: self.get_azobject(cls, obj_id, info=info),
                                      f'get_default_{cls.subobject_name()}': lambda self: self.get_default_azobject(cls),
                                      f'get_{cls.subobject_name()}s': lambda self, **kwargs: self.get_azobjects(cls, **kwargs)}))

    return containerclasses
