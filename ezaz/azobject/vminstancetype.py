
from .computesku import ComputeSku


class VmInstanceType(ComputeSku):
    @classmethod
    def azobject_name_list(cls):
        return ['vm', 'instance', 'type']

    @classmethod
    def get_resource_type(cls):
        return 'virtualMachines'

