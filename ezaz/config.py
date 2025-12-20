
import json

from abc import ABC
from abc import abstractmethod
from contextlib import suppress
from copy import copy
from functools import partial
from pathlib import Path

from . import DEFAULT_CONFIGPATH
from . import DEFAULT_CONFIGFILE
from .objproxy import BaseProxy
from .objproxy import DictProxy
from .objproxy import ListProxy


class BaseSubConfig(BaseProxy, ABC):
    __missing = object()
    _ignore_values = ([], {}, None, __missing)
    _missing_values = (None, __missing)

    @classmethod
    def _clean_value(cls, value):
        if value in cls._ignore_values:
            return None
        if isinstance(value, BaseSubConfig):
            return value.clean()
        return value

    def __init__(self, parent, target):
        self._parent = parent
        super().__init__(target,
                         dict_proxy_class=partial(DictSubConfig, self),
                         list_proxy_class=partial(ListSubConfig, self))

    @abstractmethod
    def clean(self):
        pass

    @property
    def parent(self):
        return self._parent

    @property
    def configfile(self):
        return self.parent.configfile

    @property
    @abstractmethod
    def _exception(self):
        pass

    def _value_or_missing(self, key):
        with suppress(self._exception):
            return self._target[key]
        return self.__missing

    def should_save(self, old_value, new_value):
        # Assumes old_value != new_value
        return old_value not in self._ignore_values or new_value not in self._ignore_values

    def save(self):
        return self.parent.save()


class DictSubConfig(BaseSubConfig, DictProxy):
    def clean(self):
        return {k: c for k, v in self.items() for c in [self._clean_value(v)] if c is not None} or None

    @property
    def _exception(self):
        return KeyError

    def __setitem__(self, key, value):
        old_value = self._value_or_missing(key)
        if old_value == value:
            return
        super().__setitem__(key, value)
        if self.should_save(old_value, value):
            self.save()

    def __delitem__(self, key):
        old_value = self._value_or_missing(key)
        super().__delitem__(key)
        if self.should_save(old_value, None):
            self.save()

    def setdefault(self, key, value):
        if self._value_or_missing(key) in self._missing_values:
            # We consider None value == missing key
            self[key] = value
        return self[key]

    def get_object(self, key):
        # get the specified object, or insert and return a new empty one
        return self.setdefault(key, {})

    def get_list(self, key):
        # get the specified list, or insert and return a new empty one
        return self.setdefault(key, [])


class ListSubConfig(BaseSubConfig, ListProxy):
    def clean(self):
        return [c for v in self for c in [self._clean_value(v)] if c is not None] or None

    @property
    def _exception(self):
        return IndexError

    def __setitem__(self, index, value):
        old_value = self._value_or_missing(index)
        if old_value == value:
            return
        super().__setitem__(index, value)
        if self.should_save(old_value, value):
            self.save()

    def __delitem__(self, index):
        super().__delitem__(index)
        # Will not reach here if the index is invalid, so always save
        self.save()


class Config(DictSubConfig):
    GLOBAL_CONFIG = None

    @classmethod
    def get_global_config(cls):
        # main should have set this already, fail immediately if not
        assert cls.GLOBAL_CONFIG is not None
        return cls.GLOBAL_CONFIG

    @classmethod
    def set_global_config(cls, configfile):
        assert cls.GLOBAL_CONFIG is None
        cls.GLOBAL_CONFIG = cls(configfile)

    @classmethod
    def add_argument_to_parser(cls, parser, *args, default=DEFAULT_CONFIGFILE, help=None, **kwargs):
        if help is None:
            help = 'Path to the config file, or filename in standard config dir'
        parser.add_argument(*args, default=default, help=help, **kwargs).completer = cls.completer

    @classmethod
    def completer(cls, *, prefix, **kwargs):
        path = Path(prefix).expanduser()

        if not path.is_absolute():
            return [m.removeprefix(str(DEFAULT_CONFIGPATH) + '/')
                    for m in cls.completer(prefix=str(DEFAULT_CONFIGPATH / prefix))]

        for p in (path, path.parent):
            if p.is_dir():
                return [str(f) + ('/' if f.is_dir() else '')
                        for f in p.iterdir()
                        if str(f).startswith(str(path))]

        return []

    @classmethod
    def get_configfile_path(cls, configfile):
        configpath = Path(configfile).expanduser()
        if configpath.is_absolute():
            return configpath.resolve()

        configpath = DEFAULT_CONFIGPATH.joinpath(configfile).expanduser().resolve()
        try:
            configpath.relative_to(DEFAULT_CONFIGPATH)
        except ValueError as ve:
            raise InvalidArgumentValue(f'Invalid path for configfile: {configfile}') from ve
        return configpath

    def __init__(self, configfile):
        self._configfile = self.get_configfile_path(configfile)
        super().__init__(self, self._read_config())
        # TODO - check with jsonschema

    def _read_config(self):
        try:
            return json.loads(self.configfile.read_text())
        except FileNotFoundError:
            return {}

    @property
    def configfile(self):
        return self._configfile

    def save(self):
        self.configfile.parent.mkdir(parents=True, exist_ok=True)
        self.configfile.write_text(json.dumps(self.clean() or {}) + '\n')

    def remove(self):
        self.configfile.unlink(missing_ok=True)
        self.__init__(configfile=self.configfile)
