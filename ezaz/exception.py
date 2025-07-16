

class ConfigError(Exception):
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


class AlreadyLoggedIn(Exception):
    pass


class AlreadyLoggedOut(Exception):
    pass


class NotLoggedIn(Exception):
    def __init__(self):
        super().__init__('Not logged in, please login and try again.')


class NotCreatable(Exception):
    pass


class NotDeletable(Exception):
    pass
