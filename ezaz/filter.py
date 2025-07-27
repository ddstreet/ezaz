
import json
import re

from contextlib import suppress

from .exception import InvalidFilterRegex


KEY_PREFIX = 'prefix'
KEY_SUFFIX = 'suffix'
KEY_REGEX = 'regex'

FILTER_ALL = 'all'
FILTER_DEFAULT = 'default'


class Filters:
    def __init__(self, config):
        self._config = config
        self._filters = {}

    @property
    def config(self):
        return self._config

    @property
    def is_empty(self):
        return all([not v for v in self.config.values()])

    def get_filter(self, filter_type):
        return self._get_filter(filter_type, True)

    def _get_filter(self, filter_type, create):
        with suppress(KeyError):
            return self._filters[filter_type]
        if create:
            self._filters[filter_type] = Filter(self.config.get_object(filter_type))
        else:
            self._filters[filter_type] = Filter(self.config[filter_type])
        return self._filters[filter_type]

    def del_filter(self, filter_type):
        with suppress(KeyError):
            del self._filters[filter_type]
        with suppress(KeyError):
            del self.config[filter_type]

    def check(self, filter_type, name):
        return self._check(name, FILTER_ALL) and self._check(name, filter_type, FILTER_DEFAULT)

    def _check(self, name, *filter_types):
        for filter_type in filter_types:
            with suppress(KeyError):
                # Use result of first filter that exists
                return self._get_filter(filter_type, False).check(name)
        # None of the filters exist
        return True


class Filter:
    def __init__(self, config):
        self._config = config

    def __repr__(self):
        return json.dumps(dict(self.config), indent=2)

    @property
    def config(self):
        return self._config

    @property
    def is_empty(self):
        return not (self.prefix or self.suffix or self.regex)

    def check(self, v):
        return self.check_prefix(v) and self.check_suffix(v) and self.check_regex(v)

    def check_prefix(self, v):
        return v.startswith(self.prefix) if self.prefix else True

    def check_suffix(self, v):
        return v.endswith(self.suffix) if self.suffix else True

    def check_regex(self, v):
        return re.match(self.regex, v) if self.regex else True

    def _get(self, key):
        return self.config.get(key, None)

    def _set(self, key, value):
        if value:
            self.config[key] = value
        else:
            self._del(key)

    def _del(self, key):
        with suppress(KeyError):
            del self.config[key]

    prefix = property(fget=lambda self: self._get(KEY_PREFIX),
                      fset=lambda self, v: self._set(KEY_PREFIX, v),
                      fdel=lambda self: self._del(KEY_PREFIX))

    suffix = property(fget=lambda self: self._get(KEY_SUFFIX),
                      fset=lambda self, v: self._set(KEY_SUFFIX, v),
                      fdel=lambda self: self._del(KEY_SUFFIX))

    regex = property(fget=lambda self: self._get(KEY_REGEX),
                     fset=lambda self, v: self._check_regex_pattern(v) and self._set(KEY_REGEX, v),
                     fdel=lambda self: self._del(KEY_REGEX))

    def _check_regex_pattern(self, pattern):
        try:
            if pattern:
                re.compile(pattern)
        except re.PatternError as pe:
            raise InvalidFilterRegex(pattern) from pe
        return True
