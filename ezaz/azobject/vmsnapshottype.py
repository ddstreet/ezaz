
from .computesku import ComputeSku


class VmSnapshotType(ComputeSku):
    @classmethod
    def azobject_name_list(cls):
        return ['vm', 'snapshot', 'type']

    @classmethod
    def get_resource_type(cls):
        return 'snapshots'

