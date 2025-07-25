
from ..argutil import ArgMap
from ..exception import RequiredArgument
from .command import AzSubObjectActionCommand


class RoleAssignmentCommand(AzSubObjectActionCommand):
    @classmethod
    def parent_command_cls(cls):
        from .subscription import SubscriptionCommand
        return SubscriptionCommand

    @classmethod
    def azclass(cls):
        from ..azobject.roleassignment import RoleAssignment
        return RoleAssignment

    @property
    def azobject_default_id(self):
        if self.action == 'show':
            raise RequiredArgument(self.azobject_name(), 'show')
        return super().azobject_default_id
