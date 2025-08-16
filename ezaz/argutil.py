
import argcomplete
import argparse

from abc import ABC
from abc import abstractmethod
from collections import UserDict
from contextlib import suppress
from itertools import combinations
from pathlib import Path

from .cache import Cache
from .config import Config
from .exception import ArgumentError
from .exception import DefaultConfigNotFound
from .exception import DuplicateArgument
from .exception import RequiredArgument
from .exception import RequiredArgumentGroup


class ArgMap(UserDict):
    """Dictionary that does not allow duplicate keys."""
    def __init__(self, *dicts, **kwargs):
        super().__init__()
        for d in dicts:
            self |= d
        self |= kwargs

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
    """Convert between "opt" and "arg" format.

    Convert between "opt" format (e.g. some_param) and "arg" format
    (e.g. --some-param).

    All methods accept keys in either format, but expect dicts/kwargs
    to be in opt format.

    All returned dicts will have keys in arg format.
    """
    @classmethod
    def _arg_to_opt(cls, key):
        """Convert a key to opt format (my_arg)."""
        return key.lstrip('-').replace('-', '_')

    @classmethod
    def _args_to_opts(cls, *keys, **kwargs):
        """Convert from arg format to opt format.

        If positional keys are provided, convert all to opt format and
        return a list.

        If keyword args are provided, convert all (even those with
        None values) to opt format and return a dict.

        If both positional and keyword args are provided, raise error.
        """
        if keys and kwargs:
            raise RuntimeError('Invalid use of _args_to_opts')
        if keys:
            return [cls._arg_to_opt(k) for k in keys]
        return ArgMap({cls._arg_to_opt(k): v for k, v in kwargs.items()})

    @classmethod
    def _arg_value(cls, key, args):
        """Convert the key to arg format, and return the value from
        args, or None."""
        with suppress(KeyError):
            return args[cls._opt_to_arg(key)]
        return None
 
    @classmethod
    def _opt_to_arg(cls, key):
        """Convert a key to arg format (e.g. --my-arg). Single
        characters are convert to short arg format (e.g. -f).
        """
        key = cls._arg_to_opt(key)
        if len(key) == 1:
            return f'-{key}'
        return '--' + key.replace('_', '-')

    @classmethod
    def _opts_to_args(cls, *keys, **kwargs):
        """Convert from opt format to arg format.

        If positional keys are provided, convert all to arg format and
        return a list.

        If keyword args are provided, convert all (even those with
        None values) to arg format and return a dict.

        If both positional and keyword args are provided, raise error.
        """
        if keys and kwargs:
            raise RuntimeError('Invalid use of _opts_to_args')
        if keys:
            return [cls._opt_to_arg(k) for k in keys]
        return ArgMap({cls._opt_to_arg(k): v for k, v in kwargs.items()})

    @classmethod
    def _opt_value(cls, key, opts):
        """Convert the key to opt format, and return the value from
        opts, or None."""
        with suppress(KeyError):
            return opts[cls._arg_to_opt(key)]
        return None

    @classmethod
    def required_arg_value(cls, key, opts, requiring_arg=None):
        """Return the non-None value for key, or raise
        RequiredArgument."""
        value = cls._opt_value(key, opts)
        if value is None:
            raise RequiredArgument(key, requiring_arg)
        return value

    @classmethod
    def required_arg(cls, key, opts, requiring_arg=None):
        """Return a dict with the key and non-None value, or raise
        RequiredArguemnt."""
        return ArgMap({cls._opt_to_arg(key): cls.required_arg_value(key, opts, requiring_arg)})

    @classmethod
    def required_args_one(cls, keys, opts, requiring_arg=None):
        """Return a dict with at least one of the keys with a non-None
        value, or raise RequiredArgument.
        """
        arg_group = self.optional_args(keys, opts)
        if not arg_group:
            raise RequiredArgumentGroup(keys, requiring_arg)
        return arg_group

    @classmethod
    def required_args_all(cls, keys, opts, requiring_arg=None):
        """Same as required_args_one, but all keys must be included."""
        return ArgMap(*[cls.required_arg(k, opts, requiring_arg) for k in keys])

    @classmethod
    def optional_arg_value(cls, key, opts):
        """Same as _opt_value."""
        return cls._opt_value(key, opts)

    @classmethod
    def optional_arg(cls, key, opts):
        """Return a dict with the (arg-format) key, or an empty dict
        if the key is missing or has a value of None."""
        v = cls._opt_value(key, opts)
        return ArgMap({} if v is None else {cls._opt_to_arg(key): v})

    @classmethod
    def optional_args(cls, keys, opts):
        """Return a dict with any of the (arg-format) keys in opts, or
        an empty dict. Keys with a value of None are omitted."""
        return ArgMap(*[cls.optional_arg(k, opts) for k in keys])

    @classmethod
    def optional_flag_arg(cls, key, opts):
        """Same as optional_flag_args for a single key."""
        return cls.optional_flag_args([key], opts)

    @classmethod
    def optional_flag_args(cls, keys, opts):
        """Same as optional_args, but keys with a falsy value are
        omitted, and keys with a truthy value are included with a
        value of None.

        For example:
          {'my_param': False, 'one_more': True} -> {'--one-more': None}
        """
        return ArgMap({k: None for k, v in cls.optional_args(keys, opts).items() if v})


class AzObjectInfoHelper:
    def __init__(self, azclass, info_attr=None):
        self.azclass = azclass
        self.info_attr = info_attr

    def parent(self, **opts):
        return self.azclass.get_parent_class().create_from_opts(**opts)

    def get_info_attr(self, info):
        if self.info_attr:
            return getattr(info, self.info_attr, None)
        else:
            return self.azclass.info_id(info)


class AzObjectCompleter(AzObjectInfoHelper):
    def __call__(self, *, prefix, action, parser, parsed_args, **kwargs):
        opts = vars(parsed_args)
        try:
            return map(self.get_info_attr, self.azclass.list(self.parent(**opts), **opts))
        except Exception as e:
            if opts.get('verbose', 0) > 1:
                argcomplete.warn(f'argcomplete error: {e}')
            raise


class AzObjectDefaultId(AzObjectInfoHelper):
    def __call__(self, **opts):
        with suppress(DefaultConfigNotFound):
            child = self.parent(**opts).get_default_child(self.azclass.azobject_name())
            # Remove child's self-id dest arg, as we may be called
            # from a different argconfig that conflicts (e.g. several
            # use '--name' as their self-id dest arg). Also, we want
            # the default here, not specified
            opts.pop(child.get_self_id_argconfig_dest(is_parent=False), None)
            return self.get_info_attr(child.info(**opts))
        return None


class BaseArgConfig(ArgUtil, ABC):
    def __init__(self, *, dest=None, default=None, required=None, noncmd=False):
        self._dest = dest
        self._default = default
        self._required = required
        self.noncmd = noncmd
        if self.required and self.default:
            # Note that you can have a required argument with a callable default
            raise ArgumentError('Cannot have required argument with default')

    @property
    def dest(self):
        return self._dest

    @property
    def default(self):
        return None if callable(self._default) else self._default

    def runtime_default_value(self, **opts):
        value = self._default(**opts) if callable(self._default) else self._default
        if value is None and self._required:
            self.raise_required()
        return value

    @property
    def required(self):
        return self._required and not callable(self._default)

    @abstractmethod
    def raise_required(self):
        pass

    @abstractmethod
    def add_to_parser(self, parser):
        pass

    def cmd_arg_value(self, **opts):
        value = self._opt_value(self.dest, opts)
        if value is not None:
            return value
        return self.runtime_default_value(**opts)

    def _cmd_args(self, **opts):
        return self.optional_arg(self.dest, {self.dest: self.cmd_arg_value(**opts)})

    def cmd_args(self, **opts):
        if self.noncmd:
            return {}
        return self._cmd_args(**opts)


class ArgConfig(BaseArgConfig):
    def __init__(self, *opts,
                 help=None,
                 dest=None,
                 default=None,
                 required=False,
                 hidden=False,
                 noncmd=False,
                 completer=None):
        super().__init__(dest=dest, default=default, required=required, noncmd=noncmd)

        # opts can be provided in arg or opt format
        self.opts = self._args_to_opts(*opts)
        self.help = argparse.SUPPRESS if hidden else help
        self.completer = completer

    def __repr__(self):
        return self.__class__.__name__ + '(' + (f"{', '.join(self.opts)}, " +
                                                f"help={self.help}, " +
                                                f"dest={self._dest}, " +
                                                f"default={self._default}, " +
                                                f"required={self._required}, " +
                                                f"hidden={self.help == argparse.SUPPRESS}, " +
                                                f"noncmd={self.noncmd}, " +
                                                f"completer={self.completer})")

    def raise_required(self):
        raise RequiredArgument(self.parser_argname)

    @property
    def dest(self):
        return argparse.ArgumentParser().add_argument(*self.parser_args, dest=self._dest).dest

    @property
    def parser_argname(self):
        return argparse.ArgumentParser().add_argument(*self.parser_args).dest

    @property
    def parser_args(self):
        return self._opts_to_args(*self.opts)

    @property
    def _parser_kwargs(self):
        return {}

    @property
    def parser_kwargs(self):
        return ArgMap(help=self.help,
                      dest=self.dest,
                      required=self.required,
                      default=self.default,
                      **self._parser_kwargs)

    def add_to_parser(self, parser):
        parser.add_argument(*self.parser_args, **self.parser_kwargs).completer = self.completer


class AzObjectArgConfig(ArgConfig):
    def __init__(self, *args, azclass, cmd_attr=None, completer=None, default=None, **kwargs):
        super().__init__(*args,
                         completer=completer or AzObjectCompleter(azclass),
                         default=default or AzObjectDefaultId(azclass),
                         **kwargs)
        self.azclass = azclass
        self.cmd_attr = cmd_attr

    def cmd_args_value(self, **opts):
        azobject_id = super().cmd_args_value(**opts)
        if not self.cmd_attr:
            return azobject_id
        # This is problematic, as the azobject ancestors might not be
        # the same as the cmdline's azobject, meaning the opts don't
        # lead to an instance of the azobject here
        parent = self.azclass.get_parent_class().create_from_opts(**opts)
        child = parent.get_child(self.azclass.azobject_name(), azobject_id)
        info = child.info(**opts)
        return getattr(info, self.cmd_attr, None)


class NumberArgConfig(ArgConfig):
    @property
    def _parser_kwargs(self):
        return ArgMap(type=int)


class BoolArgConfig(ArgConfig):
    @property
    def _parser_kwargs(self):
        if self.default is True:
            return ArgMap(action='store_false')
        if self.default in [False, None]:
            return ArgMap(action='store_true')
        raise ArgumentError(f'Invalid BoolArgConfig default value: {self.default}')


class FlagArgConfig(BoolArgConfig):
    def _cmd_args(self, **opts):
        return self.optional_flag_arg(self.dest, {self.dest: self.cmd_arg_value(**opts)})


class NoWaitBoolArgConfig(BoolArgConfig):
    def __init__(self, *, help=None, **kwargs):
        super().__init__('no_wait', help=help or 'Do not wait for long-running tasks to complete', **kwargs)


class NoWaitFlagArgConfig(FlagArgConfig):
    def __init__(self, *, help=None, **kwargs):
        super().__init__('no_wait', help=help or 'Do not wait for long-running tasks to complete', **kwargs)


class YesBoolArgConfig(BoolArgConfig):
    def __init__(self, *, help=None, **kwargs):
        super().__init__('y', 'yes', help=help or 'Do not prompt for confirmation', **kwargs)


class YesFlagArgConfig(FlagArgConfig):
    def __init__(self, *, help=None, **kwargs):
        super().__init__('y', 'yes', help=help or 'Do not prompt for confirmation', **kwargs)


class ConstArgConfig(ArgConfig):
    def __init__(self, *opts, const, **kwargs):
        super().__init__(*opts, **kwargs)
        self.const = const

    @property
    def _parser_kwargs(self):
        return ArgMap(action='store_const', const=self.const)


class ChoicesArgConfig(ArgConfig):
    def __init__(self, *opts, choices, **kwargs):
        super().__init__(*opts, **kwargs)
        self.choices = choices

    @property
    def _parser_kwargs(self):
        return ArgMap(choices=self.choices)


class ChoiceMapArgConfig(ArgConfig):
    def __init__(self, *opts, choicemap, **kwargs):
        super().__init__(*opts, **kwargs)
        self.choicemap = choicemap

    @property
    def _parser_kwargs(self):
        return ArgMap(choices=self.choicemap.keys())

    def cmd_arg_value(self, **opts):
        return self.choicemap.get(super().cmd_arg_value(**opts))


class FileArgConfig(ArgConfig):
    def read_file(self, **opts):
        opts[self.dest] = self.choicemap.get(opts.get(self.dest))
        return opts

    def cmd_arg_value(self, **opts):
        filename = super().cmd_arg_value(**opts)
        if not filename:
            return None

        try:
            return Path(filename).expanduser().resolve().read_text()
        except FileNotFoundError as fnfe:
            raise ArgumentError(f'File does not exist: {filename}') from fnfe


class DateTimeArgConfig(ArgConfig):
    def cmd_arg_value(self, **opts):
        datetime_expression = super().cmd_arg_value(**opts)
        if not datetime_expression:
            return None

        import dateparser
        settings=dict(TO_TIMEZONE='UTC', RETURN_AS_TIMEZONE_AWARE=True, PREFER_DATES_FROM='future')
        datetime_value = dateparser.parse(datetime_expression, settings=settings)
        if datetime_value:
            return datetime_value.strftime('%Y-%m-%dT%H:%MZ')
        raise InvalidDateTimeArgumentValue(self.parser_argname, datetime_expression)


class GroupArgConfig(BaseArgConfig):
    # Note - this is an *exclusive* group, we don't have any use for a non-exclusive group
    def __init__(self, *argconfigs, dest=None, default=None, required=False):
        self.argconfigs = argconfigs
        super().__init__(dest=dest, default=default, required=required)
        if dest and list(filter(lambda a: a._dest, argconfigs)):
            raise ArgumentError(f'Do not set dest for both GroupArgConfig and its arguments')
        if list(filter(lambda a: a._required, argconfigs)):
            raise ArgumentError(f'Do not set required for GroupArgConfig arguments')

    @property
    def opts(self):
        for argconfig in self.argconfigs:
            for opt in argconfig.opts:
                yield opt

    def group(self, parser):
        return parser.add_mutually_exclusive_group(required=self.required)

    def add_to_parser(self, parser):
        group = self.group(parser)
        for argconfig in self.argconfigs:
            argconfig.add_to_parser(group)

    @property
    def required(self):
        return super().required and not any([callable(a._default) for a in self.argconfigs])

    def raise_required(self):
        raise RequiredArgumentGroup(list(self.opts), exclusive=True)

    def is_argconfig_set(self, argconfig, opts):
        # This is used by cmd_arg_value below to determine if the
        # provided argconfig has its value != (non-callable) default,
        # or if its callable default is not None
        if argconfig.cmd_arg_value(**opts) != argconfig.default:
            return True
        return 

    def cmd_arg_value(self, **opts):
        # This is only called if dest is set for the group.
        for argconfig in self.argconfigs:
            # First, look for the first argconfig whose value is
            # different from its non-callable default (or None)
            value = argconfig.cmd_arg_value(**opts)
            if value != argconfig.default:
                return value
        for argconfig in self.argconfigs:
            # Now, look for the first argconfig whose callable default
            # is not None
            value = argconfig.runtime_default_value(**opts)
            if callable(argconfig._default) and value is not None:
                return value
        return self.runtime_default_value(**opts)

    def _cmd_args(self, **opts):
        if self.dest:
            return super()._cmd_args(**opts)
        return ArgMap(*map(lambda argconfig: argconfig.cmd_args(**opts), self.argconfigs))


class BoolGroupArgConfig(GroupArgConfig):
    def __init__(self, opt, *, dest=None, default=False, **kwargs):
        super().__init__(*self.create_argconfigs(opt, **kwargs), dest=dest or opt, default=default)

    def create_argconfigs(self, opt, help_true=None, help_false=None, help=None, **kwargs):
        return self._create_argconfigs(opt_true=opt, opt_false=f'no_{opt}',
                                       help_true=help_true or help, help_false=help_false or help,
                                       **kwargs)

    def _create_argconfigs(self, opt_true, opt_false, help_true, help_false, **kwargs):
        return [BoolArgConfig(opt_true, default=False, help=help_true, **kwargs),
                BoolArgConfig(opt_false, default=True, help=help_false, **kwargs)]


class EnableDisableGroupArgConfig(BoolGroupArgConfig):
    def create_argconfigs(self, opt, help_enable=None, help_disable=None, help=None, **kwargs):
        opt = opt.removeprefix('enable_')
        return self._create_argconfigs(opt_true=f'enable_{opt}', opt_false=f'disable_{opt}',
                                       help_true=help_enable or help, help_false=help_disable or help,
                                       **kwargs)
