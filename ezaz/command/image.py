
import re
import tempfile

from pathlib import Path

from .. import LOGGER
from ..argutil import ArgConfig
from ..argutil import ArgMap
from ..argutil import AzObjectArgConfig
from ..argutil import BoolArgConfig
from ..argutil import X509DERFileArgConfig
from ..exception import RequiredArgument
from ..qemuimg import QemuImg
from .command import ActionCommand


class ImageCommand(ActionCommand):
    @classmethod
    def command_name_list(cls):
        return ['image']

    @classmethod
    def get_default_action(cls):
        return None

    @classmethod
    def get_action_configs(cls):
        return [*super().get_action_configs(),
                cls.get_create_action_config(),
                cls.get_convert_action_config()]

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
        return [ArgConfig('f', 'file', required=True, help='Image filename'),
                ArgConfig('version', help='Image version'),
                BoolArgConfig('no-convert',
                              help='Do not convert to Azure VHD format before uploading'),
                BoolArgConfig('overwrite',
                              help='Overwrite existing storage blob (will not overwrite image version)'),
                BoolArgConfig('uefi_extend',
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

    @classmethod
    def get_convert_action_config(cls):
        return cls.make_action_config('convert',
                                      description='Convert an image file to an Azure-acceptable VHD image file',
                                      argconfigs=cls.get_convert_action_argconfigs())

    @classmethod
    def get_convert_action_argconfigs(cls):
        return [ArgConfig('f', 'file', required=True, help='Input image filename'),
                ArgConfig('o', 'output', required=True, help='Output image filename'),
                BoolArgConfig('force', help='Convert even if input image is already in Azure VHD format')]

    def create(self, file, version=None, no_convert=False, **opts):
        img = QemuImg(file, dry_run=self.dry_run)
        filename = img.filepath.name
        if not version:
            version = self._parse_file_version(filename)
        if not version:
            raise RequiredArgument('version', 'create')

        if img.is_azure_vhd_format:
            LOGGER.info(f"Image '{file}' in Azure VHD format, uploading")
        elif no_convert:
            LOGGER.warning(f"Image '{file}' not in Azure VHD format, uploading without converting")
        else:
            LOGGER.info(f"Converting image '{file}' to Azure VHD before uploading")
            with tempfile.TemporaryDirectory() as tempdir:
                vhd = Path(tempdir) / img.filepath.with_suffix('.vhd').name
                img.convert_to_azure_vhd(vhd)
                self._create(vhd.name, str(vhd), version, **opts)
                return

        self._create(filename, file, version, **opts)

    def _create(self, storage_blob, file, image_version, **opts):
        LOGGER.info(f"Uploading image '{file}'")

        from ..azobject.storageblob import StorageBlob
        blob = StorageBlob.get_instance(storage_blob=storage_blob, **opts)
        blob.create(storage_blob=storage_blob, file=file, **opts)

        LOGGER.info(f"Creating image version '{image_version}'")

        from ..azobject.imageversion import ImageVersion
        iv = ImageVersion.get_instance(image_version=image_version, **opts)
        iv.create(image_version=image_version, storage_blob=storage_blob, **opts)

    def _parse_file_version(self, filename):
        match = re.search(r'(?P<major>\d+)\.(?P<minor>\d+)(?:\.(?P<release>\d+))?', filename)
        if match:
            return f"{match['major']}.{match['minor']}.{match['release'] or '0'}"
        return None

    def convert(self, file, output, force=False, **opts):
        img = QemuImg(file, dry_run=self.dry_run)
        if img.is_azure_vhd_format and not force:
            LOGGER.warning(f"Image already in Azure VHD format: '{file}'")
        else:
            img.convert_to_azure_vhd(output)
