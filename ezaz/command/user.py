
import importlib

from functools import partial
from pathlib import Path

from .command import AzObjectActionCommand


class UserCommand(AzObjectActionCommand):
    @classmethod
    def azclass(cls):
        from ..azobject.user import User
        return User

    @classmethod
    def get_default_action(cls):
        return 'signed_in_user'

    @property
    def _base_portal_url(self):
        return f'https://portal.azure.com/#view/Microsoft_AAD_UsersAndTenants/UserProfileMenuBlade/~/overview'

    @property
    def _portal_url(self):
        return f'{self._base_portal_url}/userId/{self.azobject.azobject_id}'


# Since we are the top-level azobject, automatically create command
# classes (if needed) for all our azobject subclasses; but let's not
# get too complex, so this simply tests for the existence of a file
# named for the azclass
locals().update({command_classname: type(command_classname, (AzObjectActionCommand,), dict(azclass=classmethod(partial(lambda _azclass, cls: _azclass, azclass))))
                 for azclass in UserCommand.azclass().get_descendant_classes()
                 for command_classname in [f'{azclass.__name__}Command']
                 if not Path(__file__).parent.joinpath(f'{azclass.__name__.lower()}.py').exists()})
