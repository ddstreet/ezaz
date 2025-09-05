
import argparse

from abc import ABC
from abc import abstractmethod
from collections import UserDict
from contextlib import suppress
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from functools import cached_property
from functools import partial
from itertools import combinations
from pathlib import Path

from .cache import Cache
from .config import Config
from .exception import ArgumentError
from .exception import DefaultConfigNotFound
from .exception import DuplicateArgument
from .exception import InvalidArgumentValue
from .exception import InvalidDateTimeArgumentValue
from .exception import InvalidX509DERArgumentValue
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


class BaseArgConfig(ArgUtil, ABC):
    def __init__(self, *,
                 dest=None,
                 cmddest=None,
                 cmdvalue=None,
                 default=None,
                 required=False,
                 multiple=False,
                 noncmd=False):
        self._dest = dest
        self._cmddest = cmddest
        self._cmdvalue = cmdvalue
        self._default = default
        self._required = required
        self.multiple = multiple
        self.noncmd = noncmd
        if self.required and self.default:
            # Note that you can have a required argument with a callable default
            raise ArgumentError('Cannot have required argument with default')

    @property
    def is_group(self):
        return False

    @property
    def dest(self):
        """This is the name the argparse will set in the parsed options."""
        return self._dest

    @property
    def cmddest(self):
        """This is the name we will use for the parameter passed to az."""
        return self._cmddest or self.dest

    def cmdvalue(self, value, opts):
        """This is an external callback that may modify the value."""
        return self._cmdvalue(value, opts) if self._cmdvalue else value

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

    def get_opts_arg(self, key, opts):
        return self.optional_arg(key, opts)

    def _process_value(self, value, opts):
        return value

    def process_value(self, value, opts):
        if value is None:
            return None
        return self._process_value(value, opts)

    def _cmd_arg_value(self, **opts):
        value = self._opt_value(self.dest, opts)
        if value is None:
            value = self.runtime_default_value(**opts)
        return self.process_value(value, opts)

    def _cmd_arg_values(self, **opts):
        values = self._opt_value(self.dest, opts)
        if values is None:
            values = self.runtime_default_value(**opts)
        if values is None:
            return None
        if not isinstance(values, list):
            raise InvalidArgumentValue(self.parser_argname, values)
        return [self.process_value(v, opts) for v in values]

    def cmd_arg_value(self, **opts):
        if self.multiple:
            return self._cmd_arg_values(**opts)
        else:
            return self._cmd_arg_value(**opts)

    def _cmd_args(self, **opts):
        return self.get_opts_arg(self.cmddest, {self.cmddest: self.cmdvalue(self.cmd_arg_value(**opts), opts)})

    def cmd_args(self, **opts):
        if self.noncmd:
            return {}
        return self._cmd_args(**opts)


class ArgConfig(BaseArgConfig):
    @classmethod
    def get_args_dest(self, *args, dest=None):
        return argparse.ArgumentParser().add_argument(*args, **(dict(dest=dest) if dest else {})).dest

    def __init__(self, *opts, metavar=None, help=None, hidden=False, completer=None, **kwargs):
        super().__init__(**kwargs)

        # opts can be provided in arg or opt format
        self.opts = self._args_to_opts(*opts)
        self.help = argparse.SUPPRESS if hidden else help
        self.metavar = metavar
        self.completer = completer

    def raise_required(self):
        raise RequiredArgument(self.parser_argname)

    @property
    def dest(self):
        """This is the name the argparse will set in the parsed options."""
        return self.get_args_dest(*self.parser_args, dest=self._dest)

    @property
    def parser_argname(self):
        """This is the argument name provided to the user."""
        return self.get_args_dest(*self.parser_args)

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
                      **(dict(metavar=self.metavar) if self.metavar else {}),
                      **(dict(action='append') if self.multiple else {}),
                      **self._parser_kwargs)

    def add_to_parser(self, parser):
        parser.add_argument(*self.parser_args, **self.parser_kwargs).completer = self.completer


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
    def get_opts_arg(self, key, opts):
        return self.optional_flag_arg(key, opts)


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


class AzClassesChoicesArgConfig(ChoicesArgConfig):
    def __init__(self, *opts, azclasses, **kwargs):
        super().__init__(*opts, choices=[c.azobject_name() for c in azclasses], **kwargs)


class AzClassAncestorsChoicesArgConfig(AzClassesChoicesArgConfig):
    def __init__(self, *opts, azclass, include_self=False, **kwargs):
        azclasses = ([azclass] if include_self else []) + azclass.get_ancestor_classes()
        super().__init__(*opts, azclasses=azclasses, **kwargs)


class AzClassDescendantsChoicesArgConfig(AzClassesChoicesArgConfig):
    def __init__(self, *opts, azclass, include_self=False, **kwargs):
        azclasses = ([azclass] if include_self else []) + azclass.get_descendant_classes()
        super().__init__(*opts, azclasses=azclasses, **kwargs)


class ChoiceMapArgConfig(ArgConfig):
    def __init__(self, *opts, choicemap, **kwargs):
        super().__init__(*opts, **kwargs)
        self.choicemap = choicemap

    @property
    def _parser_kwargs(self):
        return ArgMap(choices=self.choicemap.keys())

    def _process_value(self, value, opts):
        return self.choicemap.get(value)


class FileArgConfig(ArgConfig):
    def _process_value(self, value, opts):
        try:
            return self.read_file(Path(value).expanduser().resolve())
        except FileNotFoundError as fnfe:
            raise ArgumentError(f'File does not exist: {value}') from fnfe

    def read_file(self, path):
        return path.read_text()


class BinaryFileArgConfig(FileArgConfig):
    def read_file(self, path):
        return path.read_bytes()


class X509DERFileArgConfig(BinaryFileArgConfig):
    def _process_value(self, value, opts):
        cert = super()._process_value(value, opts)

        from cryptography import x509

        try:
            x509.load_der_x509_certificate(cert)
        except ValueError:
            raise InvalidX509DERArgumentValue(self.parser_argname)

        return cert


class BaseDateTimeArgConfig(ArgConfig):
    def _get_datetime(self, value, opts):
        import dateparser
        settings=dict(TO_TIMEZONE='UTC', RETURN_AS_TIMEZONE_AWARE=True, PREFER_DATES_FROM='future')
        datetime_value = dateparser.parse(value, settings=settings)
        if datetime_value:
            return datetime_value
        raise InvalidDateTimeArgumentValue(self.parser_argname, value)


class DateTimeArgConfig(BaseDateTimeArgConfig):
    def __init__(self, *args, datetime_format=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.datetime_format = datetime_format or '%Y-%m-%dT%H:%MZ'

    def _process_value(self, value, opts):
        return self._get_datetime(value, opts).strftime(self.datetime_format)


class TimeDeltaArgConfig(BaseDateTimeArgConfig):
    def __init__(self, *args, round_seconds=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.round_seconds = round_seconds

    def _process_value(self, value, opts):
        start = datetime.now(tz=timezone.utc)
        delta = self._get_datetime(value, opts) - start
        seconds = delta.total_seconds()
        return int(seconds) if self.round_seconds else seconds


class AzObjectInfoHelper:
    def __init__(self, *args, azclass, infoattr=None, resourceprefix=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.azclass = azclass
        self.infoattr = infoattr
        self.resourceprefix = resourceprefix

    def _unprefix_opts(self, opts):
        return opts | {o.removeprefix(self.resourceprefix): opts.get(o)
                       for o in opts if o.startswith(self.resourceprefix)}

    def unprefix_opts(self, opts):
        return self._unprefix_opts(opts) if self.resourceprefix else opts

    def get_info_list(self, opts):
        opts = self.unprefix_opts(opts)
        return self.azclass.get_null_instance(**opts).list(**opts)

    def get_info(self, value, opts):
        infos = list(filter(lambda info: self.get_infoattr(info) == value, self.get_info_list(opts)))
        if len(infos) > 1:
            raise ArgumentError(f'Multiple results found with attribute {self.infoattr or "_id"} == {value}')
        return infos[0] if infos else None

    def get_infoattr(self, info):
        return getattr(info, self.infoattr or '_id', None)


class AzObjectCompleter(AzObjectInfoHelper):
    def get_azobject_completer_choices(self, **opts):
        try:
            return filter(None, map(self.get_infoattr, self.get_info_list(opts)))
        except Exception as e:
            if opts.get('verbose', 0) > 2:
                import argcomplete
                argcomplete.warn(f'argcomplete error: {e}')
                if opts.get('verbose', 0) > 3:
                    import traceback
                    argcomplete.warn(traceback.format_exc())
            raise

    def __call__(self, *, prefix, action, parser, parsed_args, **kwargs):
        return self.get_azobject_completer_choices(**vars(parsed_args))


class AzObjectDefaultId(AzObjectInfoHelper):
    def get_default_azobject_id(self, **opts):
        try:
            # Can't directly get child info, as we can be called from
            # the show command
            azobject_id = self.azclass.get_default_azobject_id(**self.unprefix_opts(opts))
        except DefaultConfigNotFound:
            return None

        if not self.infoattr:
            # Don't need to lookup custom attr
            return azobject_id

        # Can use list as it doesn't require the object's default id
        return self.get_infoattr(self.get_info(azobject_id, opts))

    def __call__(self, **opts):
        return self.get_default_azobject_id(**opts)


class AzObjectArgConfig(AzObjectInfoHelper, ArgConfig):
    completer_class = AzObjectCompleter
    default_id_class = AzObjectDefaultId

    def __init__(self,
                 *args,
                 azclass,
                 infoattr=None,
                 cmdattr=None,
                 completer=None,
                 nocompleter=False,
                 default=None,
                 nodefault=False,
                 prefix=None,
                 destprefix=None,
                 dest=None,
                 resourceprefix=None,
                 **kwargs):
        self.cmdattr = cmdattr

        if destprefix:
            if resourceprefix:
                raise ArgumentError(f'Cannot set both destprefix ({destprefix}) and resourceprefix ({resourceprefix})')
            resourceprefix = destprefix

        completer=None if nocompleter else completer or self.completer_class(azclass=azclass, infoattr=infoattr, resourceprefix=resourceprefix)
        default=None if nodefault else default or self.default_id_class(azclass=azclass, infoattr=infoattr, resourceprefix=resourceprefix)

        args = args or [azclass.azobject_name()]
        if destprefix:
            if dest:
                raise ArgumentError(f'Cannot set both dest ({dest}) and destprefix ({destprefix})')
            dest = destprefix + self.get_args_dest(*args)
        if prefix:
            args = [prefix + arg for arg in args]
        super().__init__(*args,
                         azclass=azclass,
                         infoattr=infoattr,
                         completer=completer,
                         default=default,
                         resourceprefix=resourceprefix,
                         dest=dest,
                         **kwargs)

    def _process_value(self, value, opts):
        if self.infoattr == self.cmdattr:
            return value

        info = self.get_info(value, self.unprefix_opts(opts))
        if not info:
            return None

        return getattr(info, self.cmdattr or '_id', None)


class LatestAzObjectCompleter(AzObjectCompleter):
    def get_azobject_completer_choices(self, **opts):
        choices = list(super().get_azobject_completer_choices(**opts))
        if choices:
            choices.append('latest')
        return choices


class LatestAzObjectArgConfig(AzObjectArgConfig):
    completer_class = LatestAzObjectCompleter

    def _process_value(self, value, opts):
        if value == 'latest':
            infos = sorted(self.get_info_list(opts), key=self.get_infoattr, reverse=True)
            try:
                value = self.get_infoattr(infos[0])
            except IndexError:
                value = None
        return super()._process_value(value, opts)


class BaseGroupArgConfig(BaseArgConfig):
    def __init__(self, *argconfigs, **kwargs):
        self.argconfigs = argconfigs
        super().__init__(**kwargs)

    @property
    def opts(self):
        for argconfig in self.argconfigs:
            for opt in argconfig.opts:
                yield opt

    @property
    def is_group(self):
        return True

    @property
    def exclusive(self):
        return False

    def raise_required(self):
        raise RequiredArgumentGroup(list(self.opts), exclusive=self.exclusive)

    def group(self, parser):
        return parser

    def add_to_parser(self, parser):
        group = self.group(parser)
        for argconfig in self.argconfigs:
            argconfig.add_to_parser(group)

    def cmd_args(self, **opts):
        return ArgMap(*map(lambda argconfig: argconfig.cmd_args(**opts), self.argconfigs))


class GroupArgConfig(BaseGroupArgConfig):
    def __init__(self, *argconfigs, title, description=None, shared=False, **kwargs):
        self.title = title
        self.description = description
        self.shared = shared
        super().__init__(*argconfigs, **kwargs)

    def group(self, parser):
        add_argument_group = parser.add_shared_argument_group if self.shared else parser.add_argument_group
        return add_argument_group(title=self.title, description=self.description)


class ExclusiveGroupArgConfig(GroupArgConfig):
    def __init__(self,
                 *argconfigs,
                 title=None,
                 description=None,
                 shared=False,
                 cmddest=None,
                 cmdvalue=None,
                 default=None,
                 required=False):

        super().__init__(*argconfigs,
                         title=title,
                         description=description,
                         shared=shared,
                         cmddest=cmddest,
                         cmdvalue=cmdvalue,
                         default=default,
                         required=required)

        if cmddest and list(filter(lambda a: a._dest or a._cmddest, argconfigs)):
            raise ArgumentError(f'Do not set dest/cmddest for both {self.__class__.__name__} and its arguments')
        if list(filter(lambda a: a._required, argconfigs)):
            raise ArgumentError(f'Do not set required for {self.__class__.__name__} arguments')

    @property
    def exclusive(self):
        return True

    @property
    def required(self):
        return super().required and not any([callable(a._default) for a in self.argconfigs])

    def group(self, parser):
        return super().group(parser).add_mutually_exclusive_group(required=self.required)

    def cmd_arg_value(self, **opts):
        for argconfig in self.argconfigs:
            value = argconfig.cmd_arg_value(**opts)
            if value != argconfig.default:
                return value
        return self.runtime_default_value(**opts)

    def cmd_args(self, **opts):
        if self.cmddest:
            # cmddest means we put the changed child arg value into
            # cmddest, and ignore the rest
            return self._cmd_args(**opts)
        # without cmddest, we pass along all our child args; the only
        # use of group here is exclusivity (argparse enforces that the
        # user can only provide one of our child args)
        return super().cmd_args(**opts)


class BoolGroupArgConfig(ExclusiveGroupArgConfig):
    # Create dual XXX and no_XXX args.
    # The opt param (either XXX or no_XXX) sets the value to True.
    # Examples for use:
    #   opt=prompt
    #     --prompt -> (prompt=True, help=help_yes)
    #     --no-prompt -> (prompt=False, help=help_no)
    #   opt=no_prompt
    #     --prompt -> (no_prompt=False, help=help_yes)
    #     --no-prompt -> (no_prompt=True, help=help_no)
    def __init__(self, opt, *, cmddest=None, default=False, **kwargs):
        super().__init__(*self.create_argconfigs(opt, **kwargs), cmddest=cmddest or opt, default=default)

    def create_argconfigs(self, opt, help_yes=None, help_no=None, help=None, **kwargs):
        inverse = opt.startswith('no_')
        return self._create_argconfigs(opt_true=opt,
                                       opt_false=opt.removeprefix('no_') if inverse else f'no_{opt}',
                                       help_true=(help_no if inverse else help_yes) or help,
                                       help_false=(help_yes if inverse else help_no) or help,
                                       **kwargs)

    def _create_argconfigs(self, opt_true, opt_false, help_true, help_false, **kwargs):
        return [BoolArgConfig(opt_true, default=False, help=help_true, **kwargs),
                BoolArgConfig(opt_false, default=True, help=help_false, **kwargs)]


class FlagGroupArgConfig(BoolGroupArgConfig, FlagArgConfig):
    # Same as BoolGroupArgConfig, but result is a flag instead of bool.
    pass


class EnableDisableGroupArgConfig(BoolGroupArgConfig):
    # Same as BoolGroupArgConfig, but user-facing params will be enable_XXX and disable_XXX.
    # The opt should be either enable_XXX or disable_XXX.
    def create_argconfigs(self, opt, help_enable=None, help_disable=None, help=None, **kwargs):
        inverse = opt.startswith('disable_')
        if inverse:
            opt_false = 'enable_' + opt.removeprefix('disable_')
        elif opt.startswith('enable_'):
            opt_false = 'disable_' + opt.removeprefix('enable_')
        else:
            raise ArgumentError('opt must start with enable_ or disable_')
        return self._create_argconfigs(opt_true=opt,
                                       opt_false=opt_false,
                                       help_true=(help_disable if inverse else help_enable) or help,
                                       help_false=(help_enable if inverse else help_disable) or help,
                                       **kwargs)


class AzObjectGroupArgConfig(GroupArgConfig):
    def __init__(self, *, azclass, title=None, description=None, noncmd=True, **kwargs):
        return super().__init__(*azclass.get_azobject_id_argconfigs(noncmd=noncmd, **kwargs), title=title, description=description)


class PositionalArgConfig(ArgConfig):
    def __init__(self, opt, *, help=None, default=None, required=True, multiple=False, remainder=False):
        super().__init__(opt, help=help, default=default, required=required, multiple=multiple, noncmd=True)
        self.remainder = remainder

    @property
    def parser_args(self):
        return self.opts

    @property
    def _nargs(self):
        if self.remainder:
            return dict(nargs=argparse.REMAINDER)

        if self.multiple:
            return dict(nargs='+' if self.required else '*')
        else:
            return {} if self.required else dict(nargs='?')

    @property
    def dest(self):
        return self.parser_argname

    @property
    def parser_kwargs(self):
        return ArgMap(help=self.help,
                      default=self.default,
                      **self._nargs,
                      **self._parser_kwargs)


# This allows use of arguments anywhere on the command line; the
# regular argparse requires arguments (even when using ArgumentParser
# 'parents') to strictly correspond to each subparser which results in
# unexpected and unwanted behavior when using nested subparsers.
class SharedArgumentParser(argparse.ArgumentParser):
    def __init__(self, *args, all_shared=False, shared_args=None, **kwargs):
        if all_shared:
            self.add_argument = self.add_shared_argument
        super().__init__(*args, **kwargs)
        for a in shared_args or []:
            a.add_to_parser(self)

    @cached_property
    def shared_args(self):
        return []

    def add_shared_argument(self, *args, **kwargs):
        self.shared_args.append(SharedArgument(*args, **kwargs))
        return super().add_argument(*args, **kwargs)

    def add_shared_argument_group(self, title=None, description=None):
        group = super().add_argument_group(title=title, description=description)
        self.shared_args.append(SharedArgumentGroup(group))
        return group

    def add_subparsers(self, *args, **kwargs):
        subparsers = super().add_subparsers(*args, **kwargs)
        subparsers.add_parser = partial(self._subparsers_add_parser, subparsers.add_parser)
        return subparsers

    def _subparsers_add_parser(self, add_parser, *args, **kwargs):
        parser = add_parser(*args, **kwargs)
        for p in self.shared_args:
            p.add_to_parser(parser)
        return parser

    def parse_args(self, args):
        opts = super().parse_args(args)
        for p in self.shared_args:
            opts = p.parse_shared_arg(args, opts)
        return opts


class SharedArgument:
    def __init__(self, *args, shared=True, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def __repr__(self):
        args_str = ', '.join(self.args)
        kwargs_str = ', '.join([f'{k}={v}' for k, v in self.kwargs.items()])
        return f'{self.__class__.__name__}({", ".join([args_str, kwargs_str])})'

    def add_to_parser(self, parser):
        parser.add_shared_argument(*self.args, **self.kwargs)

    def parse_shared_arg(self, args, namespace):
        import string
        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument(*self.args, **self.kwargs)
        parser.add_argument(*[a for a in [f'-{l}' for l in string.ascii_letters] if a not in self.args],
                            action='store_true',
                            dest='__ignore')
        ns = parser.parse_known_args(args)[0]
        for k, v in vars(ns).items():
            if k != '__ignore':
                setattr(namespace, k, v)
        return namespace


class SharedArgumentGroup:
    def __init__(self, group):
        self.group = group
        self.group.add_argument = partial(self._group_add_argument, group.add_argument)
        self.shared_args = []

    def __repr__(self):
        return f'{self.__class__.__name__}(title={self.title}, description={self.description})'

    def _group_add_argument(self, add_argument, *args, **kwargs):
        self.shared_args.append(SharedArgument(*args, **kwargs))
        return add_argument(*args, **kwargs)

    def add_to_parser(self, parser):
        group = parser.add_shared_argument_group(title=self.group.title, description=self.group.description)
        for arg in self.shared_args:
            group.add_argument(*arg.args, **arg.kwargs)

    def parse_shared_arg(self, args, namespace):
        for p in self.shared_args:
            namespace = p.parse_shared_arg(args, namespace)
        return namespace
