
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

from ..exception import AzCommandError
from ..exception import AzObjectExists
from ..exception import DefaultConfigNotFound
from ..exception import NoAzObjectExists
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
    def azobject_arg(cls):
        return '--' + cls.azobject_name('-')

    @classmethod
    def info_id(cls, info):
        # Most use their 'name' as their obj_id
        return info.name

    @classmethod
    def get_base_cmd(cls):
        return cls.azobject_name_list()

    @classmethod
    def get_show_cmd(cls):
        return cls.get_base_cmd() + ['show']

    @classmethod
    def get_create_cmd(cls):
        return cls.get_base_cmd() + ['create']

    @classmethod
    def get_delete_cmd(cls):
        return cls.get_base_cmd() + ['delete']

    @classmethod
    def _name_to_arg(cls, name):
        return '--' + name.replace('_', '-')

    @classmethod
    def required_arg_value(self, arg, opts, requiring_arg=None):
        with suppress(KeyError):
            value = opts[arg]
            if value is not None:
                return value
        raise RequiredArgument(arg, requiring_arg)

    @classmethod
    def required_arg(self, arg, opts, requiring_arg=None):
        return {self._name_to_arg(arg): self.required_arg_value(arg, opts, requiring_arg)}

    @classmethod
    def required_args_one(self, args, opts, requiring_arg=None):
        arg_group = {self._name_to_arg(k): v for k, v in opts.items() if k in args}
        if not arg_group:
            raise RequiredArgumentGroup(args, requiring_arg)
        return arg_group

    @classmethod
    def required_args_all(self, args, opts, requiring_arg=None):
        return dict([self.required_arg(a, opts, requiring_arg).items().next() for a in args])

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

    def get_cmd_args(self, opts):
        return {self.azobject_arg(): self.azobject_id}

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
        self.az(*self.get_create_cmd(), cmd_args=self.get_create_cmd_args(kwargs), dry_runnable=False)

    def delete(self, **kwargs):
        self.az(*self.get_delete_cmd(), cmd_args=self.get_delete_cmd_args(kwargs), dry_runnable=False)


class AzSubObject(AzObject):
    @classmethod
    def default_key(cls):
        return f'default_{cls.azobject_name()}'

    @classmethod
    def object_key(cls, obj_id):
        return f'{cls.azobject_name()}.{obj_id}'

    @classmethod
    def get_list_cmd(cls):
        return cls.get_base_cmd() + ['list']

    @classmethod
    def filter_parent_args(cls, opts):
        return opts

    def __init__(self, parent, obj_id, config, info=None):
        super().__init__(config, info=info)
        self._obj_id = obj_id
        self._parent = parent
        assert isinstance(self._parent, AzSubObjectContainer)

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

    def get_parent_subcmd_args(self, opts):
        return self.parent.get_subcmd_args(opts)

    # To add args to all action cmds, use this.
    # To add args to specific action cmds, use the action-specific ones below.
    def _get_my_cmd_args(self, opts):
        return {}

    # This adds the current object's id argument, via super() call.
    def get_my_cmd_args(self, opts):
        return self._merge_cmd_args(super().get_cmd_args(opts),
                                    self._get_my_cmd_args(opts))

    def _get_my_show_cmd_args(self, opts):
        return {}

    def get_my_show_cmd_args(self, opts):
        return self._merge_cmd_args(self.get_my_cmd_args(opts),
                                    self._get_my_show_cmd_args(opts))

    def _get_my_create_cmd_args(self, opts):
        return {}

    def get_my_create_cmd_args(self, opts):
        return self._merge_cmd_args(self.get_my_cmd_args(opts),
                                    self._get_my_create_cmd_args(opts))

    def _get_my_delete_cmd_args(self, opts):
        return {}

    def get_my_delete_cmd_args(self, opts):
        return self._merge_cmd_args(self.get_my_cmd_args(opts),
                                    self._get_my_delete_cmd_args(opts))

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

    def set_default(self, **kwargs):
        self.parent.set_azsubobject_default_id(self.azobject_name(),
                                               self.required_arg_value(self.azobject_name(), kwargs, 'set'))

    def clear_default(self, **kwargs):
        self.parent.del_azsubobject_default_id(self.azobject_name())


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

    def list(self, name, **kwargs):
        for azobject in self.get_azsubobjects(name, **kwargs):
            azobject.show()

    @classmethod
    @abstractmethod
    def get_azsubobject_classes(cls):
        pass

    @classmethod
    def get_azsubobject_classmap(cls):
        return {c.azobject_name(): c for c in cls.get_azsubobject_classes()}

    @classmethod
    def get_azsubobject_class(cls, name):
        with suppress(KeyError):
            return cls.get_azsubobject_classmap()[name]
        raise InvalidAzObjectName(f'AzObject {cls.__name__} does not contain AzObjects with name {name}')

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
                self.az_responselist(*cls.get_list_cmd(), cmd_args=self.get_list_cmd_args(cls, kwargs))]
