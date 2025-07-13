
from .account import AccountCommand
from .config import ConfigCommand
from .imagegallery import ImageGalleryCommand
from .imagedefinition import ImageDefinitionCommand
from .login import LoginCommand
from .logout import LogoutCommand
from .resourcegroup import ResourceGroupCommand
from .storageaccount import StorageAccountCommand
from .storagecontainer import StorageContainerCommand
from .vm import VMCommand


COMMANDS = [
    AccountCommand,
    ConfigCommand,
    ImageGalleryCommand,
    ImageDefinitionCommand,
    LoginCommand,
    LogoutCommand,
    ResourceGroupCommand,
    StorageAccountCommand,
    StorageContainerCommand,
    VMCommand,
]
