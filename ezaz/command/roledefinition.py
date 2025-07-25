
from .command import AzObjectActionCommand


class RoleDefinitionCommand(AzObjectActionCommand):
    @classmethod
    def azclass(cls):
        from ..azobject.roledefinition import RoleDefinition
        return RoleDefinition
