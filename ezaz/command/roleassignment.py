
from .command import AzObjectActionCommand


class RoleAssignmentCommand(AzObjectActionCommand):
    @classmethod
    def azclass(cls):
        from ..azobject.roleassignment import RoleAssignment
        return RoleAssignment
