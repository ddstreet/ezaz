
import importlib
import json
import subprocess

from abc import ABC
from abc import abstractmethod
from contextlib import suppress
from functools import partial
from functools import partialmethod

from ..exception import NotLoggedIn
from ..response import lookup_response


class AzObject(ABC):
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

    @abstractmethod
    def show_cmd(self):
        pass

    @abstractmethod
    def cmd_opts(self):
        pass

    def _get_info(self):
        return self.az_response(*self.show_cmd(), *self.cmd_opts())

    @property
    def info(self):
        if not self._info:
            self._info = self._get_info()
        return self._info

    @property
    @abstractmethod
    def verbose(self):
        pass

    @property
    @abstractmethod
    def dry_run(self):
        pass

    def _trace(self, msg):
        if self.verbose or self.dry_run:
            prefix = 'DRY-RUN: ' if self.dry_run else ''
            print(f'{prefix}{msg}')

    def _exec(self, *args, check=True, text=True, **kwargs):
        self._trace(' '.join(args))
        return None if self.dry_run else subprocess.run(args, check=check, text=text, **kwargs)

    def az(self, *args, capture_output=False, **kwargs):
        return self._exec('az', *args, capture_output=capture_output, **kwargs)

    def az_stdout(self, *args, **kwargs):
        try:
            cp = self.az(*args, capture_output=True, **kwargs)
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


class AzSubObject(AzObject):
    @classmethod
    @abstractmethod
    def subobject_name_list(cls):
        pass

    @classmethod
    def subobject_name(cls, sep='_'):
        return sep.join(cls.subobject_name_list())

    @classmethod
    def default_key(cls):
        return f'default_{cls.subobject_name()}'

    @classmethod
    def object_key(cls, obj_id):
        return f'{cls.subobject_name()}.{obj_id}'

    @classmethod
    @abstractmethod
    def list_cmd(cls):
        pass

    @classmethod
    def filter_parent_opts(cls, opts):
        return opts

    def __init__(self, parent, obj_id, config, info=None):
        super().__init__(config, info=info)
        self._obj_id = obj_id
        self._parent = parent

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


def AzSubObjectContainer(subclasses=[]):
    class InnerAzObject(AzObject):
        def subcmd_opts(self):
            with suppress(AttributeError):
                return self.parent.subcmd_opts()
            return []

    for cls in subclasses:
        assert issubclass(cls, AzSubObject)

        def get_default(cls, self):
            try:
                return self.config[cls.default_key()]
            except KeyError:
                exception = importlib.import_module('..exception', __name__)
                not_found = getattr(exception, f'{cls.__name__}ConfigNotFound')
                raise not_found()

        def set_default(cls, self, value):
            if self.config.get(cls.default_key()) != value:
                self.config[cls.default_key()] = value

        def del_default(cls, self):
            with suppress(KeyError):
                del self.config[cls.default_key()]

        setattr(InnerAzObject, cls.default_key(), property(fget=partial(get_default, cls),
                                                           fset=partial(set_default, cls),
                                                           fdel=partial(del_default, cls)))

        def get_object(self, cls, obj_id, info=None):
            return cls(self, obj_id, self.config.get_object(cls.object_key(obj_id)), info=info)

        setattr(InnerAzObject, f'get_{cls.subobject_name()}', partialmethod(get_object, cls))

        def get_default_object(self, cls):
            return getattr(self, f'get_{cls.subobject_name()}')(getattr(self, cls.default_key()))

        setattr(InnerAzObject, f'get_default_{cls.subobject_name()}', partialmethod(get_default_object, cls))

        def get_objects(self, cls):
            return [getattr(self, f'get_{cls.subobject_name()}')(cls.info_id(info), info=info)
                    for info in self.az_responselist(*cls.list_cmd(), *cls.filter_parent_opts(*self.subcmd_opts()))]

        setattr(InnerAzObject, f'get_{cls.subobject_name()}s', partialmethod(get_objects, cls))

    return InnerAzObject
