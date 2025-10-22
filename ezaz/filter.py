
import re

from abc import ABC
from abc import abstractmethod

from .dictnamespace import DictNamespace
from .exception import FilterRequiresInfo
from .exception import InvalidFilter
from .exception import InvalidFilterRegex
from .exception import InvalidFilterType


FILTER_TYPES = ['prefix', 'suffix', 'regex']


class Filter(DictNamespace, ABC):
    @classmethod
    def create_filter(cls, config=None, *, filter_type=None, filter_field=None, filter_value=None):
        filter_type = filter_type or (config or {}).get('type')
        if not filter_type:
            raise InvalidFilterType(filter_type)
        filter_cls = {
            'prefix': PrefixFilter,
            'suffix': SuffixFilter,
            'regex': RegexFilter,
        }.get(filter_type)
        if not filter_cls:
            raise InvalidFilterType(filter_type)
        return filter_cls(config, filter_field=filter_field, filter_value=filter_value)

    def __init__(self, config=None, *, filter_type=None, filter_field=None, filter_value=None):
        super().__init__(config or {})

        self.type = filter_type or getattr(self, 'type', None)
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
    def __init__(self, config=None, *, filter_type='prefix', filter_field=None, filter_value=None):
        super().__init__(config, filter_type=filter_type, filter_field=filter_field, filter_value=filter_value)

    def _check_filter_value(self, value):
        # Prefix filter with no value is invalid since it would match everything
        if not value:
            raise InvalidFilter(f'Prefix filter requires a prefix value')
        super()._check_filter_value(value)

    def _check_value(self, value):
        return value.startswith(self.value)


class SuffixFilter(Filter):
    def __init__(self, config=None, *, filter_type='suffix', filter_field=None, filter_value=None):
        super().__init__(config, filter_type=filter_type, filter_field=filter_field, filter_value=filter_value)

    def _check_filter_value(self, value):
        # Suffix filter with no value is invalid since it would match everything
        if not value:
            raise InvalidFilter(f'Suffix filter requires a suffix value')
        super()._check_filter_value(value)

    def _check_value(self, value):
        return value.endswith(self.value)


class RegexFilter(Filter):
    def __init__(self, config=None, *, filter_type='regex', filter_field=None, filter_value=None):
        super().__init__(config, filter_type=filter_type, filter_field=filter_field, filter_value=filter_value)

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
