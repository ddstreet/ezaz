
from ..argutil import ArgConfig
from ..argutil import ArgMap
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
    def get_self_id_argconfig_dest(cls, is_parent):
        return 'gallery_image_version'

    @classmethod
    def get_create_action_argconfigs(cls):
        from .storageaccount import StorageAccount
        from .storageblob import StorageBlob
        return [AzObjectArgConfig('storage_account',
                                  azclass=StorageAccount,
                                  noncmd=True,
                                  required=True,
                                  help='Storage account containing OS disk image VHD'),
                AzObjectArgConfig('image', 'storage_blob',
                                  azclass=StorageBlob,
                                  noncmd=True,
                                  required=True,
                                  help='VHD to use for the OS disk image'),
                ArgConfig('os_vhd_storage_account', hidden=True),
                ArgConfig('os_vhd_uri', required=True, hidden=True),
                NoWaitFlagArgConfig()]

    @classmethod
    def get_delete_action_argconfigs(cls):
        return [NoWaitBoolArgConfig()]

    def create(self, *, storage_account, storage_blob, **opts):
        super().create(os_vhd_storage_account=storage_account,
                       os_vhd_uri=self.os_vhd_uri(storage_account=storage_account, storage_blob=storage_blob, **opts),
                       **opts)

    def os_vhd_uri(self, *, storage_account, storage_blob, **opts):
        from .storageblob import StorageBlob
        blob = StorageBlob.create_from_opts(storage_account=storage_account, storage_blob=storage_blob, **self.azobject_creation_opts, **opts)
        return blob.url(**opts)
