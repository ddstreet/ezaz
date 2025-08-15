
from ..argutil import BoolArgConfig
from ..argutil import ChoicesArgConfig
from ..argutil import YesFlagArgConfig
from .azobject import AzCommonActionable
from .azobject import AzSubObject
from .azobject import AzFilterer
from .azobject import AzSubObjectContainer


class StorageAccount(AzCommonActionable, AzFilterer, AzSubObject, AzSubObjectContainer):
    @classmethod
    def azobject_name_list(cls):
        return ['storage', 'account']

    @classmethod
    def get_parent_class(cls):
        from .resourcegroup import ResourceGroup
        return ResourceGroup

    @classmethod
    def get_child_classes(cls):
        from .storagecontainer import StorageContainer
        from .storagekey import StorageKey
        return [StorageContainer, StorageKey]

    @classmethod
    def get_self_id_argconfig_dest(cls, is_parent):
        return 'account_name' if is_parent else 'name'

    @classmethod
    def get_create_action_argconfigs(cls):
        return [BoolArgConfig('allow_blob_public_access',
                              default=False,
                              help='Allow containers/blobs to be configured for public access'),
                BoolArgConfig('allow_shared_key_access',
                              default=False,
                              help='Allow access using storage account shared key'),
                ChoicesArgConfig('kind',
                                 choices=['BlobStorage', 'BlockBlobStorage', 'FileStorage', 'Storage', 'StorageV2'],
                                 help='Type of storage account'),
                ChoicesArgConfig('sku',
                                 choices=([f'Premium_{c}' for c in ['LRS', 'ZRS']] +
                                          [f'PremiumV2_{c}' for c in ['LRS', 'ZRS']] +
                                          [f'Standard_{c}' for c in ['GRS', 'GZRS', 'LRS', 'RAGRS', 'RAGZRS', 'ZRS']] +
                                          [f'StandardV2_{c}' for c in ['GRS', 'GZRS', 'LRS', 'ZRS']]),
                                 help='The storage account SKU.')]

    @classmethod
    def get_delete_action_argconfigs(cls):
        return [YesFlagArgConfig()]

    @property
    def allow_shared_key_access(self):
        # The default is True (i.e. None == True)
        return self.info().allowSharedKeyAccess is not False
