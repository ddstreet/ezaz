
from .account import AccountCommand
from .image import ImageCommand
from .login import LoginCommand
from .logout import LogoutCommand
from .resourcegroup import ResourceGroupCommand
from .vm import VMCommand


COMMANDS = [
    AccountCommand,
    ImageCommand,
    LoginCommand,
    LogoutCommand,
    ResourceGroupCommand,
    VMCommand,
]
