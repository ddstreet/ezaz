
from .command import AzCommonActionCommand


class RoleDefinitionCommand(AzCommonActionCommand):
    @classmethod
    def azclass(cls):
        from ..azobject.roledefinition import RoleDefinition
        return RoleDefinition
