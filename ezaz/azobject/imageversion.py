
import json
import tempfile

from ..argutil import ArgConfig
from ..argutil import ArgMap
from ..argutil import AzObjectArgConfig
from ..argutil import BoolArgConfig
from ..argutil import FileArgConfig
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
                                  cmddest='os_vhd_storage_account',
                                  required=True,
                                  help='Storage account containing OS disk image VHD'),
                AzObjectArgConfig('image', 'storage_blob',
                                  azclass=StorageBlob,
                                  dest='storage_blob',
                                  noncmd=True,
                                  required=True,
                                  help='VHD to use for the OS disk image'),
                ArgConfig('os_vhd_uri', required=True, hidden=True),
                BoolArgConfig('uefi_extend', noncmd=True, help='Add, instead of replacing, the UEFI certs'),
                FileArgConfig('uefi_pk', dest='pk', noncmd=True, help='Replace PK with provided x509 cert (default is to use first db cert)'),
                FileArgConfig('uefi_kek', dest='kek', noncmd=True, help='Replace KEK with provided x509 cert (default is to use first db cert)'),
                FileArgConfig('uefi_db', dest='db', noncmd=True, help='Replace db with provided x509 cert(s)'),
                FileArgConfig('uefi_dbx', dest='dbx', noncmd=True, help='Replace db with provided x509 cert(s) (default is empty dbx)'),
                NoWaitFlagArgConfig()]

    @classmethod
    def get_delete_action_argconfigs(cls):
        return [NoWaitBoolArgConfig()]

    def create(self, *, storage_account, storage_blob, os_vhd_uri=None, pk=None, kek=None, db=None, dbx=None, **opts):
        os_vhd_uri=os_vhd_uri or self.os_vhd_uri(storage_account=storage_account, storage_blob=storage_blob, **opts)
        if any((pk, kek, db, dbx)):
            self.deploy(storage_account, storage_blob, os_vhd_uri=os_vhd_uri, pk=pk, kek=kek, db=db, dbx=dbx, **opts)
        else:
            super().create(storage_account=storage_account, os_vhd_uri=os_vhd_uri, **opts)

    def os_vhd_uri(self, *, storage_account, storage_blob, **opts):
        from .storageblob import StorageBlob
        blob = StorageBlob.create_from_opts(storage_account=storage_account, storage_blob=storage_blob, **self.azobject_creation_opts, **opts)
        return blob.url(**opts)

    def deploy(self, *, storage_account, storage_blob, os_vhd_uri=None, uefi_extend=False, uefi_pk=None, uefi_kek=None, uefi_db=None, uefi_dbx=None, **opts):
        template = self.create_template(storage_account, storage_blob, os_vhd_uri=None, uefi_extend=False, uefi_pk=None, uefi_kek=None, uefi_db=None, uefi_dbx=None, **opts)

        from .resourcegroup import ResourceGroup
        group = ResourceGroup.create_from_opts(**self.azobject_creation_opts, **opts)

        with tempfile.NamedTemporaryFile(delete_on_close=False) as template_file:
            Path(template_file).write_text(json.dumps(template))
            group.deploy(template_file=template_file, **opts)

    def create_template(self, *, storage_account, storage_blob, os_vhd_uri, uefi_db, uefi_extend=False, uefi_pk=None, uefi_kek=None, uefi_dbx=None):
        template = {
            "$schema": "http://schema.management.azure.com/schemas/2015-01-01/deploymentTemplate.json#",
            "contentVersion": "1.0.0.0",
            "variables": {},
            "resources": [],
            "outputs": {},
        }

        image_gallery = self.parent.parent.azobject_id
        image_definition = self.parent.azobject_id
        image_version = self.azobject_id

        from .storageaccount import StorageAccount
        sa = StorageAccount.create_from_opts(storage_account=storage_account, **self.azobject_creation_opts, **opts)
        sainfo = sa.info(**opts)
        location = sainfo.location
        storage_account_type = sainfo.storageAccountType
        storage_account_id = sainfo.id

        template.get('resources').append({
            "apiVersion": "2023-07-03",
            "type": "Microsoft.Compute/galleries/images/versions",
            "dependsOn": [],
            "name": image_gallery + '/' + image_definition + '/' + image_version,
            "location": location,
            "properties": {
                "publishingProfile": {
                    "replicaCount": "1",
                    "targetRegions": [
                        {
                            "name": location,
                            "regionalReplicaCount": 1,
                            "storageAccountType": storage_account_type,
                            "excludeFromLatest": false
                        },
                    ],
                    "excludeFromLatest": false,
                    "storageAccountType": storage_account_type,
                    "replicationMode": "Full"
                },
                "storageProfile": {
                    "osDiskImage": {
                        "source": {
                            "storageAccountId": storage_account_id,
                            "uri": os_vhd_uri,
                        },
                        "hostCaching": "ReadOnly"
                    },
                },
                "safetyProfile": {
                    "allowDeletionOfReplicatedLocations": false
                },
            },
            "tags": {},
        })

        return template
