
from .computesku import ComputeSku


class VmDiskType(ComputeSku):
    @classmethod
    def azobject_name_list(cls):
        return ['vm', 'disk', 'type']

    @classmethod
    def get_resource_type(cls):
        return 'disks'

