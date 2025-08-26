
import tempfile

from pathlib import Path

from ..argutil import BoolArgConfig
from ..argutil import X509DERFileArgConfig
from ..deployment.imageversion import ImageVersionTemplate
from ..exception import DefaultConfigNotFound
from ..exception import RequiredArgument
from .command import AzSubObjectActionCommand


class ImageVersionCommand(AzSubObjectActionCommand):
    @classmethod
    def parent_command_cls(cls):
        from .imagedefinition import ImageDefinitionCommand
        return ImageDefinitionCommand

    @classmethod
    def azclass(cls):
        from ..azobject.imageversion import ImageVersion
        return ImageVersion

    @classmethod
    def get_action_configs(cls):
        return [*filter(lambda c: c.action != 'create', super().get_action_configs()),
                cls.get_create_actioncfg(cls.azclass().get_action_config('create'))]

    @classmethod
    def get_create_actioncfg(cls, azactioncfg):
        return cls.make_azaction_config(azactioncfg, argconfigs=cls.get_create_action_argconfigs())

    @classmethod
    def get_create_action_argconfigs(cls):
        return [BoolArgConfig('uefi_extend',
                              help='Add, instead of replacing, the UEFI certs'),
                X509DERFileArgConfig('uefi_pk',
                                     multiple=True,
                                     help='Replace (or extend) PK with provided x509 cert (default is to use first db cert, or no change if extending)'),
                X509DERFileArgConfig('uefi_kek',
                                     multiple=True,
                                     help='Replace (or extend) KEK with provided x509 cert (default is to use first db cert, or no change if extending)'),
                X509DERFileArgConfig('uefi_db',
                                     multiple=True,
                                     help='Replace (or extend) db with provided x509 cert(s)'),
                X509DERFileArgConfig('uefi_dbx',
                                     multiple=True,
                                     help='Replace (or extend) db with provided x509 cert(s) (default is empty dbx, or no change if extending)')]

    def create(self, **opts):
        if any(map(opts.get, ['uefi_pk', 'uefi_kek', 'uefi_db', 'uefi_dbx'])):
            return self.deploy(**opts)
        return self.get_action_config('create').do_azaction(**opts)

    def deploy(self, *, uefi_extend=False, uefi_pk=None, uefi_kek=None, uefi_db=None, uefi_dbx=None, **opts):
        try:
            self.azobject.azobject_id
        except DefaultConfigNotFound:
            raise RequiredArgument(self.azobject_name(), 'create')

        from ..azobject.storageaccount import StorageAccount
        sa = StorageAccount.get_instance(**opts)
        sainfo = sa.info()
        location = sainfo.location
        storage_account_id = sainfo.id

        actioncfg = self.get_action_config('create')
        cmd_opts = actioncfg.cmd_opts(uefi_pk=uefi_pk, uefi_kek=uefi_kek, uefi_db=uefi_db, uefi_dbx=uefi_dbx, **opts)

        pk = cmd_opts.get('uefi_pk') or []
        kek = cmd_opts.get('uefi_kek') or []
        db = cmd_opts.get('uefi_db') or []
        dbx = cmd_opts.get('uefi_dbx') or []

        if not uefi_extend:
            if not pk:
                pk = db[:1]
            if not kek:
                kek = db[:1]

        image_definition_azobject = self.parent_azobject
        image_gallery_azobject = image_definition_azobject.parent
        resource_group_azobject = image_gallery_azobject.parent

        template = ImageVersionTemplate(image_gallery_name=image_gallery_azobject.azobject_id,
                                        image_definition_name=image_definition_azobject.azobject_id,
                                        image_version_name=self.azobject_id,
                                        location=location,
                                        uefi_extend=uefi_extend,
                                        os_disk_image_storage_account_id=cmd_opts.get('os_vhd_storage_account'),
                                        os_disk_image_uri=cmd_opts.get('os_vhd_uri'),
                                        pk=pk,
                                        kek=kek,
                                        db_x509=db,
                                        dbx_x509=dbx)

        with tempfile.NamedTemporaryFile() as template_file:
            Path(template_file.name).write_text(template.to_json())
            resource_group_azobject.deploy(template_file=template_file.name, **opts)
