

class EzazException(Exception):
    pass


class ConfigError(EzazException):
    pass


class ConfigNotFound(ConfigError):
    pass


class AccountConfigNotFound(ConfigNotFound):
    pass


class SubscriptionConfigNotFound(ConfigNotFound):
    pass


class ResourceGroupConfigNotFound(ConfigNotFound):
    pass


class ImageGalleryConfigNotFound(ConfigNotFound):
    pass


class ImageDefinitionConfigNotFound(ConfigNotFound):
    pass


class StorageAccountConfigNotFound(ConfigNotFound):
    pass


class StorageContainerConfigNotFound(ConfigNotFound):
    pass


class StorageBlobConfigNotFound(ConfigNotFound):
    pass


class SshKeyConfigNotFound(ConfigNotFound):
    pass


class VMConfigNotFound(ConfigNotFound):
    pass


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


class RequiredParameter(EzazException):
    def __init__(self, param, msg=None):
        super().__init__(msg if msg else f'The parameter --{param} is required.')
