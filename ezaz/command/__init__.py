
from .account import AccountCommand
from .config import ConfigCommand
from .image import ImageCommand
from .imagegallery import ImageGalleryCommand
from .login import LoginCommand
from .logout import LogoutCommand
from .resourcegroup import ResourceGroupCommand
from .vm import VMCommand


COMMANDS = [
    AccountCommand,
    ConfigCommand,
    ImageCommand,
    ImageGalleryCommand,
    LoginCommand,
    LogoutCommand,
    ResourceGroupCommand,
    VMCommand,
]
