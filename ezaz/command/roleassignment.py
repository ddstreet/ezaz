
from .command import AzCommonActionCommand


class RoleAssignmentCommand(AzCommonActionCommand):
    @classmethod
    def azclass(cls):
        from ..azobject.roleassignment import RoleAssignment
        return RoleAssignment
