
import json
import tempfile

from pathlib import Path

from ..argutil import ArgConfig
from ..argutil import ArgMap
from ..argutil import AzObjectArgConfig
from ..argutil import BoolArgConfig
from ..argutil import X509DERFileArgConfig
from ..argutil import NoWaitBoolArgConfig
from ..argutil import NoWaitFlagArgConfig
from ..deployment.imageversion import ImageVersionTemplate
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
                                  required=True,
                                  help='Storage account containing OS disk image VHD'),
                AzObjectArgConfig('image', 'storage_blob',
                                  azclass=StorageBlob,
                                  dest='storage_blob',
                                  noncmd=True,
                                  required=True,
                                  help='VHD to use for the OS disk image'),
                ArgConfig('os_vhd_storage_account', hidden=True),
                ArgConfig('os_vhd_uri', hidden=True),
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
                NoWaitFlagArgConfig()]

    @classmethod
    def get_delete_action_argconfigs(cls):
        return [NoWaitBoolArgConfig()]

    def create(self, *, storage_account, storage_blob, os_vhd_uri=None, pk=None, kek=None, db=None, dbx=None, **opts):
        os_vhd_uri=os_vhd_uri or self.os_vhd_uri(storage_account=storage_account, storage_blob=storage_blob, **opts)
        if any((pk, kek, db, dbx)):
            self.deploy(storage_account=storage_account, storage_blob=storage_blob, os_vhd_uri=os_vhd_uri, pk=pk, kek=kek, db=db, dbx=dbx, **opts)
        else:
            super().create(os_vhd_storage_account=storage_account, os_vhd_uri=os_vhd_uri, **opts)

    def os_vhd_uri(self, *, storage_account, storage_blob, **opts):
        from .storageblob import StorageBlob
        blob = StorageBlob.get_instance(resource_group=self.parent.parent.parent.azobject_id, storage_account=storage_account, storage_blob=storage_blob)
        return blob.url(**opts)

    def deploy(self, *, storage_account, os_vhd_uri=None, uefi_extend=False, pk=None, kek=None, db=None, dbx=None, **opts):
        sa = self.parent.parent.parent.get_child('storage_account', storage_account)
        sainfo = sa.info(**opts)
        location = sainfo.location
        storage_account_id = sainfo.id

        actioncfg = self.get_action_config('create')
        pk = actioncfg.get_arg_value('pk', pk=pk) or []
        kek = actioncfg.get_arg_value('kek', kek=kek) or []
        db = actioncfg.get_arg_value('db', db=db) or []
        dbx = actioncfg.get_arg_value('dbx', dbx=dbx) or []

        if not uefi_extend:
            if not pk:
                pk = db[:1]
            if not kek:
                kek = db[:1]

        template = ImageVersionTemplate(image_gallery_name=self.parent.parent.azobject_id,
                                        image_definition_name=self.parent.azobject_id,
                                        image_version_name=self.azobject_id,
                                        location=location,
                                        uefi_extend=uefi_extend,
                                        os_disk_image_storage_account_id=storage_account_id,
                                        os_disk_image_uri=os_vhd_uri,
                                        pk=pk,
                                        kek=kek,
                                        db_x509=db,
                                        dbx_x509=dbx)

        group = self.parent.parent.parent
        with tempfile.NamedTemporaryFile(delete_on_close=False) as template_file:
            Path(template_file.name).write_text(template.to_json())
            group.deploy(template_file=template_file.name, **opts)
