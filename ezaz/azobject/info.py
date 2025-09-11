
import json
import jsonschema
import operator

from contextlib import suppress
from copy import deepcopy

from ..dictnamespace import DictNamespace
from ..exception import InvalidInfo
from ..schema import *
from ..timing import TIMESTAMP


class Info(DictNamespace):
    SAVE_KEY = 'ezaz_info_class'

    @classmethod
    def load(cls, content, verbose):
        if not content:
            return None
        try:
            obj = json.loads(content)
        except json.decoder.JSONDecodeError as jde:
            raise InvalidInfo(f'Failed to decode info: {content}') from jde
        return cls._load(obj, verbose=verbose)

    @classmethod
    def _load(cls, obj, verbose):
        infoclsname = obj.pop(cls.SAVE_KEY, None)
        if not infoclsname:
            raise InvalidInfo('Info does not contain its class name')
        infocls = globals().get(infoclsname)
        if not infocls:
            raise InvalidInfo(f'No Info class found: {infoclsname}')
        try:
            return infocls(obj, verbose=verbose)
        except jsonschema.exceptions.ValidationError as ve:
            raise InvalidInfo('Failed to validate Info json') from ve

    @classmethod
    def load_list(cls, content, verbose):
        if not content:
            return []
        try:
            objs = json.loads(content)
        except json.decoder.JSONDecodeError as jde:
            raise InvalidInfo(f'Failed to decode info list: {content}') from jde
        if not isinstance(objs, list):
            raise InvalidInfo(f'Info list is not a list: {content}')
        try:
            return [cls._load(obj, verbose) for obj in objs]
        finally:
            TIMESTAMP('Info.load_list()')

    @classmethod
    def save_list(cls, infos):
        assert all([isinstance(info, Info) for info in infos])
        return json.dumps([info._save() for info in infos])

    _verbose = 0

    def __init__(self, info, *, verbose):
        super().__init__(info)
        self._verbose = verbose

    def _save(self):
        return deepcopy(self) | {self.SAVE_KEY: self.__class__.__name__}

    def save(self):
        return json.dumps(self._save())

    # Main id attribute, will be used for azobject_id
    _id_attr = 'name'

    @property
    def _id(self):
        assert self._id_attr
        return operator.attrgetter(self._id_attr)(self)

    # Id attrs to use for this info, by verbosity levels.
    #
    # Will look like the following (except any id set to the same attr
    # as the previous one is elided):
    #
    # id0 (id1) [id2]
    #
    # Using defaults, this results in:
    #
    # name [id]
    _id0_attr = '_id'
    _id1_attr = '_id'
    _id2_attr = 'id'

    def __str__(self):
        verbose = self._verbose
        with suppress(AttributeError):
            return getattr(self, f'_str{verbose}')
        return self._str3

    @property
    def _str0(self):
        assert self._id0_attr
        return operator.attrgetter(self._id0_attr)(self)

    @property
    def _str1(self):
        extra = (operator.attrgetter(self._id1_attr)(self)
                 if self._id1_attr and self._id0_attr != self._id1_attr
                 else None)
        return f'{self._str0} ({extra})' if extra else self._str0

    @property
    def _str2(self):
        extra = (operator.attrgetter(self._id2_attr)(self)
                 if self._id2_attr and self._id1_attr != self._id2_attr
                 else None)
        return f'{self._str1} [{extra}]' if extra else self._str1

    @property
    def _str3(self):
        # At verbose=3 or higher, the full info is provided (as a json string)
        return self._jsonstr(2)


class AccountInfo(Info):
    _schema = OBJ(
        id=STR,
        name=STR,
        user=OBJ(
            name=STR,
        ),
    )


class ConfigVarInfo(Info):
    _schema = OBJ(
        name=STR,
        source=STR,
        value=STR,
    )

    _id_attr = 'id'
    _id1_attr = 'source'
    _id2_attr = 'value'


class GroupInfo(Info):
    _schema = OBJ(
        id=STR,
        name=STR,
        location=STR,
        tags=ANY(
            OBJ(),
            NULL,
        ),
    )


class ImageDefinitionInfo(Info):
    _schema = OBJ(
        id=STR,
        name=STR,
        location=STR,
        resourceGroup=STR,
        identifier=OBJ(
            offer=STR,
            publisher=STR,
            sku=STR,
        ),
        architecture=STR,
        hyperVGeneration=STR,
        osState=STR,
        osType=STR,
        tags=ANY(
            OBJ(),
            NULL,
        ),
    )


class ImageGalleryInfo(Info):
    _schema = OBJ(
        id=STR,
        name=STR,
        location=STR,
        resourceGroup=STR,
        provisioningState=STR,
        type=STR,
        identifier=OBJ(
            uniqueName=STR,
        ),
    )

    _id1_attr = 'identifier.uniqueName'


class ImageVersionInfo(Info):
    _schema = OBJ(
        id=STR,
        name=STR,
        location=STR,
        provisioningState=STR,
        publishingProfile=OBJ(
            excludeFromLatest=BOOL,
            publishedDate=STR,
            replicaCount=NUM,
            storageAccountType=STR,
            targetRegions=ARRY(
                OBJ(
                    name=STR,
                    regionalReplicaCount=NUM,
                    storageAccountType=STR,
                ),
            ),
        ),
        resourceGroup=STR,
        storageProfile=OBJ(
            osDiskImage=OBJ(),
        ),
    )


class IpConfigInfo(Info):
    _schema = OBJ(
        id=STR,
        name=STR,
        primary=BOOL,
        privateIPAddress=STR,
        publicIPAddress=OBJ(
            id=STR,
            resourceGroup=STR,
        ),
        resourceGroup=STR,
        subnet=OBJ(
            id=STR,
            resourceGroup=STR,
        ),
    )

    _id1_attr = 'privateIPAddress'


class LocationInfo(Info):
    _schema = OBJ(
        id=STR,
        name=STR,
        displayName=STR,
        regionalDisplayName=STR,
        type=STR,
    )

    _id0_attr = 'displayName'


class MarketplaceImageVersionInfo(Info):
    _schema = OBJ(
        publisher=STR,
        offer=STR,
        sku=STR,
        version=STR,
        urn=STR,
        architecture=STR,
    )

    _id_attr = 'version'
    _id1_attr = 'architecture'
    _id2_attr = 'urn'


class MarketplaceOfferInfo(Info):
    _schema = OBJ(
        id=STR,
        name=STR,
        location=STR,
    )

    _id1_attr = 'location'


class MarketplacePublisherInfo(Info):
    _schema = OBJ(
        id=STR,
        name=STR,
        location=STR,
    )

    _id1_attr = 'location'


class MarketplaceSkuInfo(Info):
    _schema = OBJ(
        id=STR,
        name=STR,
        location=STR,
    )

    _id1_attr = 'location'


class NicInfo(Info):
    _schema = OBJ(
        id=STR,
        name=STR,
        location=STR,
        resourceGroup=STR,
        resourceGuid=STR,
    )

    @property
    def primary(self):
        # Seems like it's simply missing when it's not True
        with suppress(AttributeError):
            return self.__getattr__('primary')
        return False


class PublicIpInfo(Info):
    _schema = OBJ(
        id=STR,
        name=STR,
        ipAddress=STR,
        location=STR,
        resourceGroup=STR,
        resourceGuid=STR,
    )

    _id1_attr = 'ipAddress'


class RoleAssignmentInfo(Info):
    _schema = OBJ(
        id=STR,
        name=STR,
    )


class RoleDefinitionInfo(Info):
    _schema = OBJ(
        id=STR,
        name=STR,
        roleName=STR,
        roleType=STR,
    )

    _id0_attr = 'roleName'
    _id1_attr = 'name'


class SshKeyInfo(Info):
    _schema = OBJ(
        id=STR,
        name=STR,
        location=STR,
        publicKey=STR,
        resourceGroup=STR,
        tags=ANY(
            OBJ(),
            NULL,
        ),
    )


class StorageAccountInfo(Info):
    _schema = OBJ(
        id=STR,
        name=STR,
        location=STR,
        resourceGroup=STR,
        allowSharedKeyAccess=ANY(
            BOOL,
            NULL,
        ),
        creationTime=STR,
        tags=ANY(
            OBJ(),
            NULL,
        ),
    )


class StorageBlobInfo(Info):
    _schema = OBJ(
        name=STR,
        properties=OBJ(
            blobType=STR,
            contentLength=NUM,
            contentSettings=OBJ(
                contentType=STR,
            ),
            creationTime=STR,
        ),
        tags=ANY(
            OBJ(),
            NULL,
        ),
    )


class StorageContainerInfo(Info):
    _schema = OBJ(
        name=STR,
    )

    _id2_attr = 'name'


class StorageKeyInfo(Info):
    _schema = OBJ(
        keyName=STR,
        value=STR,
        permissions=STR,
        creationTime=STR,
    )

    _id_attr = 'keyName'
    _id2_attr = '_id'


class UserInfo(Info):
    _schema = OBJ(
        id=STR,
        displayName=STR,
        userPrincipalName=STR,
    )

    _id_attr = 'id'
    _id0_attr = 'displayName'
    _id2_attr = 'userPrincipalName'


class VmInfo(Info):
    _schema = OBJ(
        id=STR,
        name=STR,
        location=STR,
        resourceGroup=STR,
        timeCreated=STR,
        vmId=STR,
        tags=ANY(
            OBJ(),
            NULL,
        ),
    )

    _id1_attr = 'vmId'


class VmInstanceInfo(Info):
    _schema = OBJ(
        id=STR,
        instanceView=OBJ(),
        location=STR,
        name=STR,
        osProfile=OBJ(
            adminUsername=STR,
            computerName=STR,
        ),
        provisioningState=STR,
        resourceGroup=STR,
        storageProfile=OBJ(
            diskControllerType=STR,
            imageReference=OBJ(),
            osDisk=OBJ(
                caching=STR,
                createOption=STR,
                deleteOption=STR,
                diskSizeGB=NUM,
                managedDisk=OBJ(
                    id=STR,
                    resourceGroup=STR,
                    storageAccountType=STR,
                ),
                name=STR,
                osType=STR,
            ),
        ),
        tags=ANY(
            OBJ(),
            NULL,
        ),
        timeCreated=STR,
        vmId=STR,
    )

    _id1_attr = 'vmId'


class VmNicInfo(Info):
    _schema = OBJ(
        id=STR,
        resourceGroup=STR,
    )

    @property
    def name(self):
        # Not sure why azure-cli can't just provide the actual name
        # field here :(
        return self.id.split('/')[-1]


class VmSkuInfo(Info):
    _schema = OBJ(['name', 'resourceType', 'locations'],
        name=STR,
        resourceType=STR,
        locations=ARRY(
            STR,
        ),
        locationInfo=ARRY(
            OBJ(
                location=STR,
            ),
        ),
        capabilities=ARRY(
            OBJ(
                name=STR,
                value=STR,
            ),
        ),
    )


def IL(info):
    return lambda infos, verbose=0: [info(i, verbose=verbose) for i in infos]

INFOS = DictNamespace({
    'account': {
        'list': IL(AccountInfo),
        'list-locations': IL(LocationInfo),
        'show': AccountInfo,
    },
    'ad': {
        'signed-in-user': {
            'show': UserInfo,
        },
        'user': {
            'list': IL(UserInfo),
            'show': UserInfo,
        },
    },
    'config': {
        'get': ConfigVarInfo,
    },
    'group': {
        'create': GroupInfo,
        'list': IL(GroupInfo),
        'show': GroupInfo,
    },
    'network': {
        'nic': {
            'ip-config': {
                'list': IL(IpConfigInfo),
                'show': IpConfigInfo,
            },
            'list': IL(NicInfo),
            'show': NicInfo,
        },
        'public-ip': {
            'list': IL(PublicIpInfo),
            'show': PublicIpInfo,
        },
    },
    'role': {
        'assignment': {
            'create': RoleAssignmentInfo,
            'list': IL(RoleAssignmentInfo),
        },
        'definition': {
            'list': IL(RoleDefinitionInfo),
            'show': RoleDefinitionInfo,
        },
    },
    'sig': {
        'create': ImageGalleryInfo,
        'list': IL(ImageGalleryInfo),
        'image-definition': {
            'create': ImageDefinitionInfo,
            'list': IL(ImageDefinitionInfo),
            'show': ImageDefinitionInfo,
        },
        'image-version': {
            'create': ImageVersionInfo,
            'list': IL(ImageVersionInfo),
            'show': ImageVersionInfo,
        },
        'show': ImageGalleryInfo,
    },
    'sshkey': {
        'create': SshKeyInfo,
        'show': SshKeyInfo,
        'list': IL(SshKeyInfo),
    },
    'storage': {
        'account': {
            'create': StorageAccountInfo,
            'keys': {
                'list': IL(StorageKeyInfo),
            },
            'list': IL(StorageAccountInfo),
            'show': StorageAccountInfo,
        },
        'blob': {
            'create': StorageBlobInfo,
            'list': IL(StorageBlobInfo),
            'show': StorageBlobInfo,
        },
        'container': {
            'list': IL(StorageContainerInfo),
            'show': StorageContainerInfo,
        },
    },
    'vm': {
        'create': VmInfo,
        'get-instance-view': VmInstanceInfo,
        'image': {
            'list': IL(MarketplaceImageVersionInfo),
            'list-offers': IL(MarketplaceOfferInfo),
            'list-publishers': IL(MarketplacePublisherInfo),
            'list-skus': IL(MarketplaceSkuInfo),
        },
        'list': IL(VmInfo),
        'list-skus': IL(VmSkuInfo),
        'nic': {
            'list': IL(VmNicInfo),
            'show': NicInfo,
        },
        'show': VmInfo,
    },
})

def info_class(cmd):
    with suppress(AttributeError):
        return operator.attrgetter('.'.join(cmd))(INFOS)
    raise RuntimeError(f"No Response type found for cmd: {' '.join(cmd)}")
