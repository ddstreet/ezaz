
from ..argutil import ArgConfig
from ..argutil import AzObjectArgConfig
from ..argutil import NoWaitBoolArgConfig
from ..argutil import NoWaitFlagArgConfig
from .azobject import AzCommonActionable
from .azobject import AzSubObject


class ImageVersion(AzCommonActionable, AzSubObject):
    @classmethod
    def azobject_name_list(cls):
        return ['image', 'version']

    @classmethod
    def get_cmd_base(cls):
        return ['sig', 'image-version']

    @classmethod
    def get_parent_class(cls):
        from .imagedefinition import ImageDefinition
        return ImageDefinition

    @classmethod
    def get_self_id_argconfig_cmddest(cls, is_parent):
        return 'gallery_image_version'

    @classmethod
    def get_create_action_argconfigs(cls):
        from .storageaccount import StorageAccount
        from .storageblob import StorageBlob
        from .storagecontainer import StorageContainer
        return [AzObjectArgConfig('storage_account',
                                  azclass=StorageAccount,
                                  cmdattr='id',
                                  cmddest='os_vhd_storage_account',
                                  help='Storage account containing OS disk image VHD'),
                AzObjectArgConfig('storage_container',
                                  azclass=StorageContainer,
                                  noncmd=True,
                                  help='Storage container containing OS disk image VHD'),
                AzObjectArgConfig('image', 'storage_blob',
                                  azclass=StorageBlob,
                                  dest='storage_blob',
                                  cmddest='os_vhd_uri',
                                  cmdvalue=cls.os_vhd_uri,
                                  required=True,
                                  help='VHD to use for the OS disk image'),
                NoWaitFlagArgConfig()]

    @classmethod
    def os_vhd_uri(cls, storage_blob, opts):
        opts['storage_blob'] = storage_blob
        parent = cls.get_parent_instance(**opts)

        from .storageblob import StorageBlob
        blob = StorageBlob.get_instance(**opts)

        return blob.url(**opts)

    @classmethod
    def get_delete_action_argconfigs(cls):
        return [NoWaitBoolArgConfig()]
