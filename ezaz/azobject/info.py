
import jsonschema
import operator

from contextlib import suppress

from ..dictnamespace import DictNamespace
from ..schema import *


class Info(DictNamespace):
    _schema = None
    _verbose = {}

    def __init__(self, info, *, verbose=0):
        super().__init__(info)
        # Use a class dict instead of an instance attr, so it doesn't
        # show up in our verbose string repr
        self._verbose[id(self)] = verbose

        assert self._schema
        jsonschema.validate(info, self._schema)

    # Default to using 'name' as unique id
    _azobject_id_attr = 'name'

    @property
    def _azobject_id(self):
        assert self._azobject_id_attr
        return operator.attrgetter(self._azobject_id_attr)(self)

    def __str__(self):
        verbose = self._verbose[id(self)]
        with suppress(AttributeError):
            return getattr(self, f'_str{verbose}')
        return self._str3

    _str0_attr = '_azobject_id'

    @property
    def _str0(self):
        assert self._str0_attr
        return operator.attrgetter(self._str0_attr)(self)

    _str1_attr = '_azobject_id'

    @property
    def _str1(self):
        extra = (operator.attrgetter(self._str1_attr)(self)
                 if self._str1_attr and self._str0_attr != self._str1_attr
                 else None)
        return f'{self._str0} ({extra})' if extra else self._str0

    _str2_attr = 'id'

    @property
    def _str2(self):
        extra = (operator.attrgetter(self._str2_attr)(self)
                 if self._str2_attr and self._str1_attr != self._str2_attr
                 else None)
        return f'{self._str1} [{extra}]' if extra else self._str1

    @property
    def _str3(self):
        return repr(self)


class AccountInfo(Info):
    _schema = OBJ(
        id=STR,
        name=STR,
        user=OBJ(
            name=STR,
        ),
    )

    _azobject_id_attr = 'id'
    _str0_attr = 'user.name'


class UserInfo(Info):
    _schema = OBJ(
        id=STR,
        displayName=STR,
        userPrincipalName=STR,
    )

    _azobject_id_attr = 'id'
    _str0_attr = 'displayName'
    _str2_attr = 'userPrincipalName'


class RoleDefinitionInfo(Info):
    _schema = OBJ(
        id=STR,
        name=STR,
        roleName=STR,
        roleType=STR,
    )

    _str0_attr = 'roleName'
    _str1_attr = 'name'


class RoleAssignmentInfo(Info):
    _schema = OBJ(
        id=STR,
        name=STR,
    )

    _str0_attr = 'roleDefinitionName'
    _str1_attr = 'name'


class ConfigVarInfo(Info):
    _schema = OBJ(
        name=STR,
        source=STR,
        value=STR,
    )


class LocationInfo(Info):
    _schema = OBJ(
        id=STR,
        name=STR,
        displayName=STR,
        regionalDisplayName=STR,
        type=STR,
    )

    _str0_attr = 'displayName'
    _str1_attr = 'name'


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


class ImageGalleryInfo(Info):
    _schema = OBJ(
        id=STR,
        name=STR,
        location=STR,
        resourceGroup=STR,
        provisioningState=STR,
        type=STR,
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


class StorageKeyInfo(Info):
    _schema = OBJ(
        keyName=STR,
        value=STR,
        permissions=STR,
        creationTime=STR,
    )

    @property
    def _azobject_id(self):
        return self.keyName


class StorageContainerInfo(Info):
    _schema = OBJ(
        name=STR,
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


class VMInfo(Info):
    _schema = OBJ(
        id=STR,
        name=STR,
        location=STR,
        resourceGroup=STR,
        securityProfile=OBJ(
            securityType=STR,
            uefiSettings=OBJ(
                secureBootEnabled=BOOL,
                vTpmEnabled=BOOL,
            ),
        ),
        timeCreated=STR,
        vmId=STR,
        tags=ANY(
            OBJ(),
            NULL,
        ),
    )


class VMInstanceInfo(Info):
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
        securityProfile=OBJ(
            securityType=STR,
            uefiSettings=OBJ(
                secureBootEnabled=BOOL,
                vTpmEnabled=BOOL,
            ),
        ),
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


def IL(info):
    return lambda infos, verbose=0: [info(i, verbose=verbose) for i in infos]

INFOS = DictNamespace({
    'account': {
        'show': AccountInfo,
        'list': IL(AccountInfo),
        'list-locations': IL(LocationInfo),
    },
    'ad': {
        'user': {
            'show': UserInfo,
            'list': IL(UserInfo),
        },
        'signed-in-user': {
            'show': UserInfo,
        }
    },
    'config': {
        'get': ConfigVarInfo,
    },
    'group': {
        'create': GroupInfo,
        'show': GroupInfo,
        'list': IL(GroupInfo),
    },
    'role': {
        'definition': {
            'show': RoleDefinitionInfo,
            'list': IL(RoleDefinitionInfo),
        },
        'assignment': {
            'create': RoleAssignmentInfo,
            'list': IL(RoleAssignmentInfo),
        },
    },
    'sig': {
        'create': ImageGalleryInfo,
        'show': ImageGalleryInfo,
        'list': IL(ImageGalleryInfo),
        'image-definition': {
            'create': ImageDefinitionInfo,
            'show': ImageDefinitionInfo,
            'list': IL(ImageDefinitionInfo),
        },
        'image-version': {
            'create': ImageVersionInfo,
            'show': ImageVersionInfo,
            'list': IL(ImageVersionInfo),
        },
    },
    'storage': {
        'account': {
            'create': StorageAccountInfo,
            'show': StorageAccountInfo,
            'list': IL(StorageAccountInfo),
            'keys': {
                'list': IL(StorageKeyInfo),
            },
        },
        'container': {
            'show': StorageContainerInfo,
            'list': IL(StorageContainerInfo),
        },
        'blob': {
            'create': StorageBlobInfo,
            'show': StorageBlobInfo,
            'list': IL(StorageBlobInfo),
        },
    },
    'sshkey': {
        'create': SshKeyInfo,
        'show': SshKeyInfo,
        'list': IL(SshKeyInfo),
    },
    'vm': {
        'create': VMInfo,
        'show': VMInfo,
        'list': IL(VMInfo),
        'get-instance-view': VMInstanceInfo,
    },
})

def info_class(cmd):
    with suppress(AttributeError):
        return operator.attrgetter('.'.join(cmd))(INFOS)
    raise RuntimeError(f"No Response type found for cmd: {' '.join(cmd)}")
