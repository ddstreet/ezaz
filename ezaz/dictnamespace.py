
import json
import jsonschema

from abc import ABC
from abc import abstractmethod
from collections.abc import Iterable
from collections.abc import MutableMapping
from collections.abc import MutableSequence
from contextlib import suppress
from copy import copy
from copy import deepcopy
from functools import cached_property
from functools import partial


class Shim(ABC):
    @property
    @abstractmethod
    def _shim_real_value(self):
        pass

    def __copy__(self):
        return copy(self._shim_real_value)

    def __deepcopy__(self, memo):
        return deepcopy(self._shim_real_value, memo)

    def __repr__(self):
        return json.dumps(self._shim_real_value, indent=2)


# Iterable namespace with direct r/w backing by a dict, including contained dicts and lists
class DictNamespace(Shim, Iterable):
    _real_value = None
    _shim_dict = None
    _schema = None

    def __init__(self, obj):
        super().__init__()
        self._real_value = obj
        self._shim_dict = DictShim(obj, dict_shim_class=DictNamespace)
        self._validate()

    def _validate(self):
        if self._schema:
            jsonschema.validate(self._real_value, self._schema)

    @property
    def _shim_real_value(self):
        return self._real_value

    def __missing__(self, attr):
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{attr}'")

    def __getattr__(self, attr):
        with suppress(KeyError):
            return self._shim_dict[attr]
        self.__missing__(attr)

    def __setattr__(self, attr, value):
        if attr in dir(self):
            super().__setattr__(attr, value)
        else:
            self._shim_dict[attr] = value

    def __delattr__(self, attr):
        if attr in dir(self):
            super().__delattr__(attr)
        else:
            try:
                self._shim_dict.pop(attr)
            except KeyError:
                self.__missing__(attr)

    def __iter__(self):
        return iter(self._shim_dict)


class BaseShim(Shim):
    def __init__(self,
                 real,
                 *,
                 dict_shim_class=None,
                 list_shim_class=None,
                 dict_test=lambda v: isinstance(v, dict),
                 list_test=lambda v: isinstance(v, list)):

        super().__init__()
        self.real = real

        self.dict_test = dict_test
        self.dict_shim_class = dict_shim_class or partial(DictShim,
                                                          dict_shim_class=dict_shim_class,
                                                          list_shim_class=list_shim_class,
                                                          dict_test=dict_test,
                                                          list_test=list_test)

        self.list_test = list_test
        self.list_shim_class = list_shim_class or partial(ListShim,
                                                          dict_shim_class=dict_shim_class,
                                                          list_shim_class=list_shim_class,
                                                          dict_test=dict_test,
                                                          list_test=list_test)

        assert self.shim_test_real(), f'Unexpected object type {type(self.real)}'
        self._setup()

    @abstractmethod
    def shim_test_real(self):
        pass

    @abstractmethod
    def _setup(self):
        pass

    @property
    @abstractmethod
    def shim(self):
        pass

    @property
    def _shim_real_value(self):
        return self.real

    def __setitem__(self, key, value):
        self.real[key] = self.unshim_value(value)
        self.shim_and_set_value(key, self.real[key])

    def __len__(self):
        return len(self.real)

    def shim_value(self, value):
        if self.dict_test(value):
            return self.dict_shim_class(value)
        if self.list_test(value):
            return self.list_shim_class(value)
        return value

    def shim_and_set_value(self, key, value):
        value = self.shim_value(value)
        if isinstance(value, Shim):
            self.shim[key] = value
        return value

    def unshim_value(self, value):
        if isinstance(value, Shim):
            return value._shim_real_value
        return value


class DictShim(BaseShim, MutableMapping):
    def shim_test_real(self):
        return self.dict_test(self.real)

    def _setup(self):
        for k, v in self.real.items():
            self[k] = v

    @cached_property
    def shim(self):
        return {}

    def __getitem__(self, key):
        with suppress(KeyError):
            return self.shim[key]
        return self.shim_and_set_value(key, self.real[key])

    def __delitem__(self, key):
        with suppress(KeyError):
            del self.shim[key]
        del self.real[key]

    def __iter__(self):
        return iter(self.real)


class ListShim(BaseShim, MutableSequence):
    def shim_test_real(self):
        return self.list_test(self.real)

    def _setup(self):
        for k, v in enumerate(self.real):
            self[k] = v

    __marker = object()

    @cached_property
    def shim(self):
        return [self.__marker] * len(self)

    def __getitem__(self, index):
        with suppress(IndexError):
            value = self.shim[index]
            if value is not self.__marker:
                return value
        return self.shim_and_set_value(index, self.real[index])

    def __delitem__(self, index):
        with suppress(IndexError):
            self.shim.pop(index)
        self.real.pop(index)

    def insert(self, index, value):
        self.shim.insert(index, self.shim_value(value))
        self.real.insert(index, value)
