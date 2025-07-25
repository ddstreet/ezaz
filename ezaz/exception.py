

class EzazException(Exception):
    pass


class NoDefaultAction(EzazException):
    pass


class ChoiceError(EzazException):
    pass


class NoChoices(ChoiceError):
    pass


class NoneOfTheAboveChoice(ChoiceError):
    pass


class CacheError(EzazException):
    pass


class CacheMiss(CacheError):
    pass


class CacheExpired(CacheError):
    pass


class FilterError(EzazException):
    pass


class InvalidFilter(FilterError):
    pass


class InvalidFilterRegex(InvalidFilter):
    def __init__(self, regex):
        super().__init__(f"Invalid regex: '{regex}'")


class AzCommandError(EzazException):
    def __init__(self, cmd, stdout=None, stderr=None):
        super().__init__(f'az command failed: {" ".join(cmd)}\n{stderr}')
        self.cmd = cmd
        self.stdout = stdout
        self.stderr = stderr


class NoAzObjectExists(EzazException):
    def __init__(self, obj_name, obj_id):
        super().__init__(f'{obj_name} (id: {obj_id}) does not exist.')


class AzObjectExists(EzazException):
    def __init__(self, obj_name, obj_id):
        super().__init__(f'{obj_name} (id: {obj_id}) already exists.')


class NullAzObject(EzazException):
    def __init__(self, func):
        super().__init__(f'Internal error: null object attempt to use {func}')


class InvalidAzObjectName(EzazException):
    pass


class ConfigError(EzazException):
    pass


class ConfigNotFound(ConfigError):
    pass


class DefaultConfigNotFound(ConfigNotFound):
    def __init__(self, azcls):
        super().__init__(f"Default configuration for {azcls.azobject_text()} not found.")
        self.azobject_class = azcls


class AlreadyLoggedIn(EzazException):
    def __init__(self, info):
        super().__init__(f'You are already logged in as {info}')


class AlreadyLoggedOut(EzazException):
    def __init__(self):
        super().__init__('You are already logged out')


class NotLoggedIn(EzazException):
    def __init__(self):
        super().__init__('Not logged in, please login and try again.')


class UnsupportedAction(EzazException):
    def __init__(self, cls, action=None):
        if action:
            super().__init__(f'Object type {cls.azobject_text()} does not support action {action}.')
        else:
            super().__init__(f'Object type {cls.azobject_text()} is not {self._actionable}.')

    @property
    def _actionable(self):
        return None


class NotCreatable(UnsupportedAction):
    @property
    def _actionable(self):
        return 'creatable'


class NotDeletable(UnsupportedAction):
    @property
    def _actionable(self):
        return 'deletable'


class NotListable(UnsupportedAction):
    @property
    def _actionable(self):
        return 'listable'


class NotDownloadable(UnsupportedAction):
    @property
    def _actionable(self):
        return 'downloadable'


class ArgumentError(EzazException):
    def _arg(self, arg):
        return arg if arg.startswith('-') else f"--{arg.replace('_', '-')}"

    def _args(self, args):
        return ', '.join([self._arg(a) for a in args])


class RequiredArgument(ArgumentError):
    def __init__(self, arg, required_by=None, **kwargs):
        super().__init__(self._msg(arg, required_by, **kwargs))

    def _msg(self, arg, by, **kwargs):
        return f'The argument {self._arg(arg)} is required{self._by(by)}.'

    def _by(self, required_by):
        return f' by {required_by}' if required_by else ''


class RequiredArgumentGroup(RequiredArgument):
    def __init__(self, args, required_by=None, exclusive=False, **kwargs):
        super().__init__(args, required_by=required_by, exclusive=exclusive, **kwargs)

    def _msg(self, args, by, exclusive, **kwargs):
        return f'{"One" if exclusive else "At least one"} of the arguments ({self._args(args)}) are required{self._by(by)}.'


class DuplicateArgument(ArgumentError):
    def __init__(self, arg, value_a, value_b):
        super().__init__(f'The argument {self._arg(arg)} was added multiple times: {value_a} and {value_b}')


class InvalidArgument(ArgumentError):
    def __init__(self, arg):
        super().__init__(f'The argument {self._arg(arg)} is invalid.')


class InvalidArgumentValue(ArgumentError):
    def __init__(self, arg, value):
        super().__init__(f'The argument {self._arg(arg)} value {value} is invalid.')


class InvalidDateTimeArgumentValue(ArgumentError):
    def __init__(self, arg, value):
        super().__init__(f'The argument {self._arg(arg)} date/time expression was not understood: {value}')


class InvalidX509DERArgumentValue(ArgumentError):
    def __init__(self, arg):
        super().__init__(f'The argument {self._arg(arg)} value is not a DER-format X509 certificate')
