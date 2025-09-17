
from ..argutil import AzObjectMultiArgConfig
from .computesku import ComputeSku


class VmInstanceType(ComputeSku):
    @classmethod
    def azobject_name_list(cls):
        return ['vm', 'instance', 'type']

    @classmethod
    def get_resource_type(cls):
        return 'virtualMachines'

    @classmethod
    def get_vm_instance_type_capability_argconfigs_group(cls, **kwargs):
        return AzObjectMultiArgConfig(dict(instance_type=dict(infoattr=None,
                                                              help='Use this specific instance type'),
                                           instance_cpus=dict(infoattr=cls.get_capability_infogetter('vCPUs'),
                                                              help='Use instance type with this many CPUs'),
                                           instance_mem_gb=dict(infoattr=cls.get_capability_infogetter('MemoryGB'),
                                                                help='Use instance type with this many GB of memory'),
                                           instance_architecture=dict(infoattr=cls.get_capability_infogetter('CpuArchitectureType'),
                                                                      help='Use instance type with this CPU architecture'),
                                           instance_hyperv_generation=dict(infoattr=cls.get_capability_infogetter('HyperVGenerations'),
                                                                           help='Use instance type running under this Hyper-V generation')),
                                      azclass=cls,
                                      **kwargs)
