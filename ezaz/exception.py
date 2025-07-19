
import types


class EzazException(Exception):
    pass


class ConfigError(EzazException):
    pass


class ConfigNotFound(ConfigError):
    pass


class DefaultConfigNotFound(ConfigNotFound):
    def __init__(self):
        super().__init__(f"Default configuration for {getattr(self, 'azobjectname', 'Config')} not found.")


AZOBJECT_TYPES = ['Account', 'Subscription', 'ResourceGroup', 'ImageGallery', 'ImageDefinition', 'StorageAccount', 'StorageContainer', 'StorageBlob', 'SshKey', 'VM']

for cls in AZOBJECT_TYPES:
    clsdfltname = f'{cls}DefaultConfigNotFound'
    globals()[clsdfltname] = type(clsdfltname, (DefaultConfigNotFound,), {'azobjectname': cls})


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
    def _arg(arg):
        return f"--{arg.replace('_', '-')}"


class RequiredArgument(ArgumentError):
    def __init__(self, arg, required_by):
        by = f' by {self._arg(required_by)}' if required_by else ''
        super().__init__(f'The argument {self._arg(arg)} is required{by}.')


class DuplicateArgument(ArgumentError):
    def __init__(self, arg, value_a, value_b):
        super().__init__(f'The argument {self._arg(arg)} was added multiple times: {value_a} and {value_b}')
