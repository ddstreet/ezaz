
import base64

from ..schema import *
from . import DeploymentTemplate


class ImageVersionTemplate(DeploymentTemplate):
    """Deployment template for an ImageVersion.

    https://learn.microsoft.com/en-us/azure/templates/microsoft.compute/2024-03-03/galleries/images/versions?pivots=deployment-language-arm-template
    """
    DEFAULT_API_VERSION = '2024-03-03'

    def __init__(self, **parameters):
        super().__init__(**parameters)
        self |= self.resources(**parameters)
        self.validate()

    def resources(self, *, image_gallery_name, image_definition_name, image_version_name, location, api_version=None, **parameters):
        return dict(
            resources=[
                dict(
                    apiVersion=api_version or self.DEFAULT_API_VERSION,
                    type='Microsoft.Compute/galleries/images/versions',
                    name=f'{image_gallery_name}/{image_definition_name}/{image_version_name}',
                    location=location,
                    properties=dict(
                        **self.security_profile(**parameters),
                        **self.storage_profile(**parameters),
                        **self.publishing_profile(**parameters),
                        **self.safety_profile(**parameters),
                    ),
                )
            ]
        )

    def security_profile(self, **parameters):
        return dict(
            securityProfile=dict(
                **self.uefi_settings(**parameters),
            )
        )

    def uefi_settings(self, **parameters):
        return dict(
            uefiSettings=dict(
                **self.signature_template_names(**parameters),
                **self.additional_signatures(**parameters),
            )
        )

    def signature_template_names(self, *, uefi_extend, **parameters):
        return dict(
            signatureTemplateNames=[
                'MicrosoftUefiCertificateAuthorityTemplate'
                if uefi_extend else
                'NoSignatureTemplate'
            ]
        )

    def additional_signatures(self, **parameters):
        return dict(
            additionalSignatures=dict(
                **self.pk(**parameters),
                **self.kek(**parameters),
                **self.db(**parameters),
                **self.dbx(**parameters),
            )
        )

    def b64(self, data):
        return base64.standard_b64encode(data).decode('ascii')

    def x509(self, certs):
        return dict(type='x509', value=[self.b64(c) for c in certs])

    def sha256(self, hashes):
        return dict(type='sha256', value=[self.b64(h) for h in hashes])

    def pk(self, *, pk=None, **parameters):
        return dict(pk=self.x509(pk)) if pk else {}

    def kek(self, *, kek=None, **parameters):
        return dict(kek=[self.x509(kek)]) if kek else {}

    def db(self, *, db_x509=[], db_sha256=[], **parameters):
        if not db_x509 and not db_sha256:
            return {}
        return dict(
            db=(([self.x509(db_x509)] if db_x509 else []) +
                ([self.sha256(db_sha256)] if db_sha256 else [])),
        )

    def dbx(self, *, dbx_x509=[], dbx_sha256=[], **parameters):
        if not dbx_x509 and not dbx_sha256:
            return {}
        return dict(
            dbx=(([self.x509(dbx_x509)] if dbx_x509 else []) +
                 ([self.sha256(dbx_sha256)] if dbx_sha256 else [])),
        )

    def storage_profile(self, **parameters):
        return dict(
            storageProfile=dict(
                **self.os_disk_image(**parameters),
                **self.data_disk_images(**parameters),
            ),
        )

    def os_disk_image(self, **parameters):
        return dict(
            osDiskImage=dict(
                **self.os_disk_image_source(**parameters),
            ),
        )

    def os_disk_image_source(self, **parameters):
        vm_id = self.os_disk_image_source_vm_id(**parameters)
        storage_uri = self.os_disk_image_source_storage_uri(**parameters)
        if not any((vm_id, storage_uri)):
            raise RuntimeError(f'Cannot create template without either os_disk_image_vm_id or (os_disk_image_storage_account_id and os_disk_image_uri)')
        return dict(source=dict(**vm_id, **storage_uri))

    def os_disk_image_source_vm_id(self, *, os_disk_image_vm_id=None, **parameters):
        if os_disk_image_vm_id:
            return dict(id=os_disk_image_vm_id)
        return {}

    def os_disk_image_source_storage_uri(self, *, os_disk_image_storage_account_id=None, os_disk_image_uri=None, **parameters):
        if os_disk_image_storage_account_id and os_disk_image_uri:
            return dict(
                storageAccountId=os_disk_image_storage_account_id,
                uri=os_disk_image_uri,
            )
        return {}

    def data_disk_images(self, **parameters):
        return {}

    def publishing_profile(self, **parameters):
        return {}

    def safety_profile(self, **parameters):
        return {}

    @property
    def schema(self):
        return OBJ(
            contentVersion=STR,
            resources=ARRY(
                OBJ(
                    apiVersion=STR,
                    type=STR,
                    name=STR,
                    location=STR,
                    properties=OBJ(['securityProfile', 'storageProfile'],
                        securityProfile=OBJ(
                            uefiSettings=OBJ(['additionalSignatures'],
                                signatureTemplateNames=ARRY(STR,),
                                additionalSignatures=OBJ(['db'],
                                    pk=OBJ(type=STR, value=ARRY(STR,),),
                                    kek=ARRY(OBJ(type=STR, value=ARRY(STR,),),),
                                    db=ARRY(OBJ(type=STR, value=ARRY(STR,),),),
                                    dbx=ARRY(OBJ(type=STR, value=ARRY(STR,),),),
                                ),
                            ),
                        ),
                        publishingProfile=OBJ(
                        ),
                        storageProfile=OBJ(
                            osDiskImage=OBJ(['source'],
                                hostCaching=STR,
                                source=ANY(
                                    OBJ(id=STR,),
                                    OBJ(storageAccountId=STR, uri=STR,)
                                ),
                            ),
                        ),
                        safetyProfile=OBJ(
                            allowDeletionOfReplicatedLocations=BOOL,
                        ),
                    ),
                ),
            ),
        )
