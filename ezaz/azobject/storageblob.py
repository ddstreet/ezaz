
from ..argutil import ArgConfig
from ..argutil import ChoicesArgConfig
from ..argutil import DateTimeArgConfig
from ..argutil import FlagArgConfig
from ..argutil import ArgMap
from ..exception import AzObjectExists
from .azobject import AzCommonActionable
from .azobject import AzSubObject


class StorageBlob(AzCommonActionable, AzSubObject):
    @classmethod
    def azobject_name_list(cls):
        return ['storage', 'blob']

    @classmethod
    def get_parent_class(cls):
        from .storagecontainer import StorageContainer
        return StorageContainer

    @classmethod
    def get_self_id_argconfig_cmddest(cls, is_parent):
        return 'name'

    @classmethod
    def get_action_configs(cls):
        return [*super().get_action_configs(),
                cls.make_action_config('download',
                                       description=f'Download a {cls.azobject_text()}'),
                cls.make_action_config('url',
                                       az='stdout',
                                       dry_runnable=True,
                                       description=f'Get the {cls.azobject_text()} access URL (without SAS)'),
                cls.make_action_config('sas',
                                       az='stdout',
                                       dry_runnable=True,
                                       cmd=cls.get_cmd_base() + ['generate-sas'],
                                       description=f'Get the {cls.azobject_text()} access URL (with SAS)')]

    @classmethod
    def get_create_action_az(cls):
        return 'none'

    @classmethod
    def get_create_action_aliases(cls):
        return ['upload']

    @classmethod
    def get_create_action_cmd(cls):
        return cls.get_cmd_base() + ['upload']

    @classmethod
    def get_create_action_description(cls):
        return f'Upload a {cls.azobject_text()}'

    @classmethod
    def get_create_action_argconfigs(cls):
        return [ArgConfig('f', 'file', required=True, help='File to upload'),
                ChoicesArgConfig('type', choices=['append', 'block', 'page'], help='Type of blob to create'),
                FlagArgConfig('no_progress', help='Do not show upload progress bar'),
                FlagArgConfig('overwrite', help='Overwrite an existing blob')]

    @classmethod
    def create_handler(cls, actioncfg, opts):
        if not opts.get(cls.azobject_name()):
            opts[cls.azobject_name()] = opts.get('file')
        return actioncfg._do_action(**opts)

    def create_pre(self, opts):
        try:
            return super().create_pre(opts)
        except AzObjectExists:
            if opts.get('overwrite'):
                return None
            raise

    @classmethod
    def get_download_action_argconfigs(cls):
        return [ArgConfig('f', 'file', required=True, help='File to download to'),
                FlagArgConfig('no_progress', help='Do not show download progress bar')]

    @classmethod
    def download_handler(cls, actioncfg, opts):
        if not opts.get(cls.azobject_name()):
            opts[cls.azobject_name()] = opts.get('file')
        return actioncfg._do_action(**opts)

    @classmethod
    def get_sas_action_argconfigs(cls):
        return [DateTimeArgConfig('expiry', help='When the SAS URL expires.'),
                FlagArgConfig('without_uri',
                              default=True,
                              dest='full_uri',
                              help='Provide only the SAS token, without URL'),
                ArgConfig('permissions',
                          default='r',
                          help=('Permissions allowed using the SAS URL. Allowed values: (a)dd (c)reate '
                                '(d)elete (e)xecute (i)set_immutability_policy (m)ove (r)ead (t)ag '
                                '(w)rite (x)delete_previous_version (y)permanent_delete.'))]

    def url(self, **opts):
        return self.do_action_config_instance_action('url', opts).strip().strip('"')

    def sas(self, **opts):
        return self.do_action_config_instance_action('sas', opts).strip().strip('"')
