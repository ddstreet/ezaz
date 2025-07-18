
import importlib
import json
import subprocess

from abc import ABC
from abc import abstractmethod
from contextlib import suppress
from functools import partial
from functools import partialmethod

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

    def _required_arg(self, arg, msg, **kwargs):
        try:
            return kwargs[arg]
        except KeyError:
            raise RequiredArgument(arg, msg)

    def required_arg_by_arg(self, arg, requiring_arg, **kwargs):
        msg = f'The --{requiring_arg.replace("_", "-")} argument requires --{arg.replace("_", "-")}'
        return self._required_arg(arg, msg, **kwargs)

    def required_arg(self, arg, **kwargs):
        return self._required_arg(arg, msg=None, **kwargs)

    def _exec(self, *args, check=True, dry_runnable=True, **kwargs):
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

    def get_cmd_opts(self, **kwargs):
        return []

    def get_show_cmd_opts(self, **kwargs):
        return self.get_cmd_opts(**kwargs)

    def get_create_cmd_opts(self, **kwargs):
        return self.get_cmd_opts(**kwargs)

    def get_delete_cmd_opts(self, **kwargs):
        return self.get_cmd_opts(**kwargs)

    def _get_info(self):
        return self.az_response(*self.get_show_cmd(), *self.get_show_cmd_opts())

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
        self.az(*self.get_create_cmd(), *self.get_create_cmd_opts(**kwargs), dry_runnable=False)

    def delete(self, **kwargs):
        self.az(*self.get_delete_cmd(), *self.get_delete_cmd_opts(**kwargs), dry_runnable=False)


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
    def filter_parent_opts(cls, *opts):
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

    def get_parent_subcmd_opts(self, **kwargs):
        with suppress(AttributeError):
            return self.parent.get_subcmd_opts(**kwargs)
        return []

    def get_my_cmd_opts(self, **kwargs):
        return []

    def get_my_show_cmd_opts(self, **kwargs):
        return self.get_my_cmd_opts(**kwargs)

    def get_my_create_cmd_opts(self, **kwargs):
        return self.get_my_cmd_opts(**kwargs)

    def get_my_delete_cmd_opts(self, **kwargs):
        return self.get_my_cmd_opts(**kwargs)

    def get_cmd_opts(self, **kwargs):
        return self.get_parent_subcmd_opts(**kwargs) + self.get_my_cmd_opts(**kwargs)

    def get_show_cmd_opts(self, **kwargs):
        return self.get_parent_subcmd_opts(**kwargs) + self.get_my_show_cmd_opts(**kwargs)

    def get_create_cmd_opts(self, **kwargs):
        return self.get_parent_subcmd_opts(**kwargs) + self.get_my_create_cmd_opts(**kwargs)

    def get_delete_cmd_opts(self, **kwargs):
        return self.get_parent_subcmd_opts(**kwargs) + self.get_my_delete_cmd_opts(**kwargs)


def AzSubObjectContainer(children=[]):
    class InnerAzObject(AzObject):
        def get_my_subcmd_opts(self, **kwargs):
            return self.get_my_cmd_opts(**kwargs)

        def get_subcmd_opts(self, **kwargs):
            if isinstance(self, AzSubObject):
                return self.get_parent_subcmd_opts(**kwargs) + self.get_my_subcmd_opts(**kwargs)
            return self.get_my_subcmd_opts(**kwargs)

        def get_list_cmd_opts(self, cls, **kwargs):
            return cls.filter_parent_opts(*self.get_subcmd_opts(**kwargs))

        # TODO - rework this to directly call classmethod cls.list()
        def list(self, cls, **kwargs):
            return self.az_responselist(*cls.get_list_cmd(), *self.get_list_cmd_opts(cls, **kwargs))

    for cls in children:
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

        def get_objects(self, cls, **kwargs):
            return [getattr(self, f'get_{cls.subobject_name()}')(cls.info_id(info), info=info)
                    for info in self.list(cls, **kwargs)]

        setattr(InnerAzObject, f'get_{cls.subobject_name()}s', partialmethod(get_objects, cls))

    return InnerAzObject
