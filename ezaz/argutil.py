
from collections import UserDict
from contextlib import suppress

from .exception import DuplicateArgument
from .exception import RequiredArgument
from .exception import RequiredArgumentGroup


class ArgMap(UserDict):
    def __init__(self, *dicts):
        super().__init__()
        for d in dicts:
            self |= d

    def _check_dup_keys(self, other):
        dupkeys = self.keys() & other.keys()
        if dupkeys:
            k = list(dupkeys)[0]
            raise DuplicateArgument(k, self.data[k], other[k])

    def __setitem__(self, key, value):
        self._check_dup_keys({key: value})
        super().__setitem__(key, value)

    def __or__(self, other):
        self._check_dup_keys(other)
        return super().__or__(other)

    def __ror__(self, other):
        self._check_dup_keys(other)
        return super().__ror__(other)

    def __ior__(self, other):
        self._check_dup_keys(other)
        return super().__ior__(other)


class ArgUtil:
    @classmethod
    def _name_to_arg(cls, name):
        return '--' + name.replace('_', '-')

    @classmethod
    def _opts_to_args(cls, **kwargs):
        return cls.optional_args(kwargs.keys(), kwargs)

    @classmethod
    def _opts_to_flag_args(cls, **kwargs):
        return cls.optional_flag_args(kwargs.keys(), kwargs)

    @classmethod
    def required_arg_value(cls, arg, opts, requiring_arg=None):
        with suppress(KeyError):
            value = opts[arg]
            if value is not None:
                return value
        raise RequiredArgument(arg, requiring_arg)

    @classmethod
    def required_arg(cls, arg, opts, requiring_arg=None):
        return ArgMap({cls._name_to_arg(arg): cls.required_arg_value(arg, opts, requiring_arg)})

    @classmethod
    def required_args_one(cls, args, opts, requiring_arg=None):
        arg_group = self.optional_args(args, opts)
        if not arg_group:
            raise RequiredArgumentGroup(args, requiring_arg)
        return arg_group

    @classmethod
    def required_args_all(cls, args, opts, requiring_arg=None):
        return ArgMap(*[cls.required_arg(a, opts, requiring_arg) for a in args])

    @classmethod
    def optional_arg(cls, arg, opts):
        return cls.optional_args([arg], opts)

    @classmethod
    def optional_args(cls, args, opts):
        return ArgMap(*[{cls._name_to_arg(a): opts[a]} for a in args if opts.get(a, None) is not None])

    @classmethod
    def optional_flag_arg(cls, arg, opts):
        return cls.optional_flag_args([arg], opts)

    @classmethod
    def optional_flag_args(cls, args, opts):
        return ArgMap(*[{cls._name_to_arg(a): None} for a in args if opts.get(a, False)])
