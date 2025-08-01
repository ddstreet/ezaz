

class EzazException(Exception):
    pass


class NoActionConfigMethod(EzazException):
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
    def __init__(self, cpe):
        super().__init__(f'az command failed: {" ".join(cpe.cmd)}\n{cpe.stderr}')
        self.cpe = cpe


class NoAzObjectExists(EzazException):
    def __init__(self, obj_name, obj_id):
        super().__init__(f'{obj_name} (id: {obj_id}) does not exist.')


class AzObjectExists(EzazException):
    def __init__(self, obj_name, obj_id):
        super().__init__(f'{obj_name} (id: {obj_id}) already exists.')


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
    pass


class AlreadyLoggedOut(EzazException):
    pass


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
    def __init__(self, arg, required_by=None):
        by = f' by {required_by}' if required_by else ''
        super().__init__(f'The argument {self._arg(arg)} is required{by}.')


class RequiredArgumentGroup(RequiredArgument):
    def __init__(self, arg, required_by=None, exclusive=False):
        by = f' by {required_by}' if required_by else ''
        super().__init__(f'{"One" if exclusive else "At least one"} of the arguments ({self._args(args)}) are required{by}.')


class DuplicateArgument(ArgumentError):
    def __init__(self, arg, value_a, value_b):
        super().__init__(f'The argument {self._arg(arg)} was added multiple times: {value_a} and {value_b}')


class InvalidArgument(ArgumentError):
    def __init__(self, arg):
        super().__init__(f'The argument {self._arg(arg)} is invalid.')


class InvalidArgumentValue(ArgumentError):
    def __init__(self, arg, value):
        super().__init__(f'The argument {self._arg(arg)} value {value} is invalid.')
