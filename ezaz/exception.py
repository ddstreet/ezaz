

class EzazException(Exception):
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


class NotCreatable(EzazException):
    def __init__(self, object_type):
        super().__init__(f'Object type {object_type} is not creatable.')


class NotDeletable(EzazException):
    def __init__(self, object_type):
        super().__init__(f'Object type {object_type} is not deletable.')


class ArgumentError(EzazException):
    def _arg(self, arg):
        return f"--{arg.replace('_', '-')}"

    def _args(self, args):
        return ', '.join([self._arg(a) for a in args])


class RequiredArgument(ArgumentError):
    def __init__(self, arg, required_by):
        by = f' by {self._arg(required_by)}' if required_by else ''
        super().__init__(f'The argument {self._arg(arg)} is required{by}.')


class RequiredArgumentGroup(ArgumentError):
    def __init__(self, args, required_by):
        by = f' by {self._arg(required_by)}' if required_by else ''
        super().__init__(f'At least one of the arguments ({self._args(args)}) are required{by}.')


class DuplicateArgument(ArgumentError):
    def __init__(self, arg, value_a, value_b):
        super().__init__(f'The argument {arg} was added multiple times: {value_a} and {value_b}')
