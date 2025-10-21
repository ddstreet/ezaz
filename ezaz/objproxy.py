
import json

from abc import ABC
from abc import abstractmethod
from collections.abc import Mapping
from collections.abc import MutableMapping
from collections.abc import MutableSequence
from collections.abc import Sequence
from contextlib import suppress
from functools import cached_property
from functools import partial


class ObjectProxy(ABC):
    @property
    @abstractmethod
    def _proxy(self):
        pass

    @property
    @abstractmethod
    def _target(self):
        pass

    def __bool__(self):
        return bool(self._target)

    def __str__(self):
        return self._to_json(2)

    def __repr__(self):
        return str(self)

    def _to_json(self, indent=None):
        return json.dumps(self._target, indent=indent)

    @abstractmethod
    def __hash__(self):
        pass

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return hash(self) == hash(other)
        return False


class BaseProxy(ObjectProxy):
    _marker = object()

    def __init__(self,
                 target,
                 *,
                 dict_proxy_class=None,
                 list_proxy_class=None,
                 dict_test=lambda v: isinstance(v, Mapping),
                 list_test=lambda v: isinstance(v, MutableSequence)):

        super().__init__()
        self.__target = target

        self._dict_test = dict_test
        self._dict_proxy_class = dict_proxy_class or partial(DictProxy,
                                                             dict_proxy_class=dict_proxy_class,
                                                             list_proxy_class=list_proxy_class,
                                                             dict_test=dict_test,
                                                             list_test=list_test)

        self._list_test = list_test
        self._list_proxy_class = list_proxy_class or partial(ListProxy,
                                                             dict_proxy_class=dict_proxy_class,
                                                             list_proxy_class=list_proxy_class,
                                                             dict_test=dict_test,
                                                             list_test=list_test)

        assert self._proxy_test_target(), f'Unexpected type {type(self._target)}'

    @property
    @abstractmethod
    def _proxy(self):
        pass

    @property
    def _target(self):
        return self.__target

    @abstractmethod
    def _proxy_test_target(self):
        pass

    def __len__(self):
        return len(self._target)

    def __setitem__(self, key, value):
        proxy_value, value = self._parse_value(value)
        self._target[key] = value
        self._set_proxy_value(key, proxy_value)

    def _set_proxy_value(self, key, value):
        self._proxy[key] = value

    def _parse_value(self, value):
        proxy_value = self._marker
        if isinstance(value, ObjectProxy):
            proxy_value = value
            value = proxy_value._target, 
        elif self._dict_test(value):
            proxy_value = self._dict_proxy_class(value)
        elif self._list_test(value):
            proxy_value = self._list_proxy_class(value)
        return (proxy_value, value)


class DictProxy(BaseProxy, MutableMapping):
    def _proxy_test_target(self):
        return self._dict_test(self._target)

    @cached_property
    def _proxy(self):
        return {}

    def _set_proxy_value(self, key, value):
        if value is self._marker:
            with suppress(KeyError):
                del self._proxy[key]
        else:
            super()._set_proxy_value(key, value)

    def __getitem__(self, key):
        with suppress(KeyError):
            return self._proxy[key]
        proxy_value, value = self._parse_value(self._target[key])
        if proxy_value is self._marker:
            return value
        self._proxy[key] = proxy_value
        return proxy_value

    def __delitem__(self, key):
        with suppress(KeyError):
            del self._proxy[key]
        del self._target[key]

    def __iter__(self):
        return iter(self._target)

    def __hash__(self):
        return sum((hash(k) + hash(v) for k, v in self.items()))


class ListProxy(BaseProxy, MutableSequence):
    def _proxy_test_target(self):
        return self._list_test(self._target)

    @cached_property
    def _proxy(self):
        return [self._marker] * len(self)

    def __getitem__(self, index):
        with suppress(IndexError):
            value = self._proxy[index]
            if value is not self._marker:
                return value
        proxy_value, value = self._parse_value(self._target[index])
        if proxy_value is self._marker:
            return value
        self._proxy[index] = proxy_value
        return proxy_value

    def __delitem__(self, index):
        with suppress(IndexError):
            self._proxy.pop(index)
        self._target.pop(index)

    def insert(self, index, value):
        proxy_value, value = self._parse_value(value)
        self._proxy.insert(index, proxy_value)
        self._target.insert(index, value)

    def __hash__(self):
        return sum(map(hash, iter(self)))
