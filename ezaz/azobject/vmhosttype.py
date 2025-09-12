
from .computesku import ComputeSku


class VmHostType(ComputeSku):
    @classmethod
    def azobject_name_list(cls):
        return ['vm', 'host', 'type']

    @classmethod
    def get_resource_type(cls):
        return 'hostGroups/hosts'

