
import re

from abc import ABC
from abc import abstractmethod

from .dictnamespace import DictNamespace
from .exception import FilterRequiresInfo
from .exception import InvalidFilter
from .exception import InvalidFilterRegex
from .exception import InvalidFilterType


class Filter(DictNamespace, ABC):
    @classmethod
    def FILTER_CLASSES(cls):
        return [PrefixFilter, ValueFilter, SuffixFilter, RegexFilter, ContainsFilter]

    @classmethod
    def FILTER_TYPES(cls):
        return {filter_cls.FILTER_TYPE(): filter_cls for filter_cls in cls.FILTER_CLASSES()}

    @classmethod
    @abstractmethod
    def FILTER_TYPE(cls):
        pass

    @classmethod
    def get_filter_class(cls, filter_type):
        try:
            return cls.FILTER_TYPES()[filter_type]
        except KeyError:
            raise InvalidFilterType(filter_type)

    @classmethod
    def create_filter(cls, config=None, *, filter_type=None, filter_field=None, filter_value=None):
        filter_type = filter_type or (config or {}).get('type')
        if not filter_type:
            raise InvalidFilterType(filter_type)
        return cls.get_filter_class(filter_type)(config, filter_field=filter_field, filter_value=filter_value)

    def __init__(self, config=None, *, filter_field=None, filter_value=None):
        super().__init__(config or {})

        self.type = self.FILTER_TYPE()
        self.field = filter_field or getattr(self, 'field', None)
        self.value = filter_value or getattr(self, 'value', None)

    def __repr__(self):
        return f"{self.type}({(self.field + '=') if self.field else ''}{self.value})"

    def __setattr__(self, attr, value):
        if attr == 'value':
            self._check_filter_value(value)
        super().__setattr__(attr, value)

    def _check_filter_value(self, value):
        if not isinstance(value, str):
            raise InvalidFilter(f"Invalid value type '{type(value)}': '{value}'")

    def check(self, info):
        value = self._get_field_value(info)
        if value is None:
            return False
        return self._check_value(value)

    def check_id(self, info_id):
        if self.field:
            raise FilterRequiresInfo()
        if info_id is None:
            return False
        return self._check_value(info_id)

    @abstractmethod
    def _check_value(self, value):
        pass

    @property
    def requires_info(self):
        return bool(self.field)

    def _get_field_value(self, info):
        if self.field:
            return info._path_attr_getter(self.field)(info) or ''
        else:
            return info._id


class PrefixFilter(Filter):
    @classmethod
    def FILTER_TYPE(cls):
        return 'prefix'

    def _check_filter_value(self, value):
        # Prefix filter with no value is invalid since it would match everything
        if not value:
            raise InvalidFilter(f'Prefix filter requires a prefix value')
        super()._check_filter_value(value)

    def _check_value(self, value):
        return value.startswith(self.value)


class SuffixFilter(Filter):
    @classmethod
    def FILTER_TYPE(cls):
        return 'suffix'

    def _check_filter_value(self, value):
        # Suffix filter with no value is invalid since it would match everything
        if not value:
            raise InvalidFilter(f'Suffix filter requires a suffix value')
        super()._check_filter_value(value)

    def _check_value(self, value):
        return value.endswith(self.value)


class RegexFilter(Filter):
    @classmethod
    def FILTER_TYPE(cls):
        return 'regex'

    def _check_filter_value(self, value):
        # Regex filter value can be the empty string, but cannot be None
        if value is None:
            raise InvalidFilter(f'Regex filter requires a regex value (or empty string)')
        try:
            re.compile(value)
        except re.PatternError as pe:
            raise InvalidFilterRegex(value) from pe
        super()._check_filter_value(value)

    def _check_value(self, value):
        return re.search(self.value, value)
