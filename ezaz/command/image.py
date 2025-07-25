
import re

from ..argutil import ArgConfig
from ..argutil import ArgMap
from ..argutil import AzObjectArgConfig
from ..argutil import BoolArgConfig
from ..argutil import X509DERFileArgConfig
from ..exception import RequiredArgument
from .command import ActionCommand


class ImageCommand(ActionCommand):
    @classmethod
    def command_name_list(cls):
        return ['image']

    @classmethod
    def get_action_configmap(cls):
        return ArgMap(super().get_action_configmap(),
                      create=cls.get_create_action_config())

    @classmethod
    def get_create_action_config(cls):
        return cls.make_action_config('create',
                                      description='Create a new image version using a VHD file',
                                      argconfigs=cls.get_create_action_argconfigs())

    @classmethod
    def get_create_action_argconfigs(cls):
        from ..azobject.subscription import Subscription
        from ..azobject.resourcegroup import ResourceGroup
        from ..azobject.imagegallery import ImageGallery
        from ..azobject.imagedefinition import ImageDefinition
        from ..azobject.storageaccount import StorageAccount
        from ..azobject.storagecontainer import StorageContainer
        return [ArgConfig('f', 'file', required=True, help='VHD file'),
                ArgConfig('version', help='Image version'),
                BoolArgConfig('uefi_extend',
                              noncmd=True,
                              help='Add, instead of replacing, the UEFI certs'),
                X509DERFileArgConfig('uefi_pk',
                                     dest='pk',
                                     multiple=True,
                                     help='Replace (or extend) PK with provided x509 cert (default is to use first db cert, or no change if extending)'),
                X509DERFileArgConfig('uefi_kek',
                                     dest='kek',
                                     multiple=True,
                                     help='Replace (or extend) KEK with provided x509 cert (default is to use first db cert, or no change if extending)'),
                X509DERFileArgConfig('uefi_db',
                                     dest='db',
                                     multiple=True,
                                     help='Replace (or extend) db with provided x509 cert(s)'),
                X509DERFileArgConfig('uefi_dbx',
                                     dest='dbx',
                                     multiple=True,
                                     help='Replace (or extend) db with provided x509 cert(s) (default is empty dbx, or no change if extending)'),
                AzObjectArgConfig('subscription', azclass=Subscription, hidden=True),
                AzObjectArgConfig('resource_group', azclass=ResourceGroup, hidden=True),
                AzObjectArgConfig('storage_account', azclass=StorageAccount, hidden=True),
                AzObjectArgConfig('storage_container', azclass=StorageContainer, hidden=True),
                AzObjectArgConfig('image_gallery', azclass=ImageGallery, hidden=True),
                AzObjectArgConfig('image_definition', azclass=ImageDefinition, hidden=True)]

    def create(self, **opts):
        filename = self.required_arg_value('file', opts)
        version = self.optional_arg_value('version', opts) or self.parse_file_version(filename)
        if not version:
            raise RequiredArgument('version', 'create')

        from ..azobject.storageblob import StorageBlob
        blob = StorageBlob.get_instance(storage_blob=filename, **opts)
        blob.create(**opts)

        from ..azobject.imageversion import ImageVersion
        iv = ImageVersion.get_instance(image_version=version, **opts)
        opts['storage_account'] = blob.parent.parent.azobject_id
        iv.create(storage_blob=blob.azobject_id, **opts)

    def parse_file_version(self, filename):
        match = re.search(r'\d+\.\d+\.\d+', filename)
        if match:
            return match.group(0)
        return None
