
import json
import jsonschema
import operator

from contextlib import suppress
from itertools import chain
from functools import cache

from .objproxy import DictProxy
from .objproxy import ObjectProxy


# Iterable namespace with direct r/w backing by a dict, including contained dicts and lists
class DictNamespace:
    __slots__ = ('_dict_proxy',)
    _schema = None

    @classmethod
    @cache
    def __all_slots(cls):
        return tuple(set(chain(*(getattr(c, '__slots__', ()) for c in cls.__mro__))))

    @classmethod
    def _path_attr_getter(self, path):
        class PathDictNamespaceAttrGetter:
            def __call__(self, obj):
                if not obj:
                    return None
                assert isinstance(obj, DictNamespace)
                with suppress(AttributeError):
                    return operator.attrgetter(path)(obj)
                return None
        return PathDictNamespaceAttrGetter()

    def __init__(self, obj):
        super().__init__()
        self._dict_proxy = DictProxy(obj._target if isinstance(obj, ObjectProxy) else obj,
                                     dict_proxy_class=DictNamespace)
        self._validate()

    def __str__(self):
        return str(self._dict_proxy)

    def __repr__(self):
        return str(self)

    def __hash__(self):
        return hash(self._dict_proxy)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return hash(self) == hash(other)
        return False

    def _to_object(self):
        return self._dict_proxy._target

    def _to_json(self, indent=None):
        return self._dict_proxy._to_json(indent=indent)

    def _validate(self):
        if self._schema:
            jsonschema.validate(self._dict_proxy._target, self._schema)

    def __bool__(self):
        return bool(self._dict_proxy)

    def __missing__(self, attr):
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{attr}'")

    def __getattr__(self, attr):
        if attr in self.__all_slots():
            super().__getattr__(attr)
        else:
            with suppress(KeyError):
                return self._dict_proxy[attr]
            self.__missing__(attr)

    def __setattr__(self, attr, value):
        if attr in self.__all_slots():
            super().__setattr__(attr, value)
        else:
            self._dict_proxy[attr] = value

    def __delattr__(self, attr):
        if attr in self.__all_slots():
            super().__delattr__(attr)
        else:
            del self._dict_proxy[attr]
