
from ..argutil import ArgMap
from ..exception import RequiredArgument
from .command import AzCommonActionCommand


class RoleAssignmentCommand(AzCommonActionCommand):
    @classmethod
    def parent_command_cls(cls):
        from .subscription import SubscriptionCommand
        return SubscriptionCommand

    @classmethod
    def azclass(cls):
        from ..azobject.roleassignment import RoleAssignment
        return RoleAssignment
