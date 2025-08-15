
import jsonschema

from abc import ABC
from abc import abstractmethod
from collections import UserList

from .dictnamespace import DictNamespace
from .schema import *


def response_id(response):
    if response._schema in [AccountInfo]:
        return response.id
    if response._schema in [StorageKeyInfo]:
        return response.keyName
    # Most objects use their 'name' field as their unique id
    return response.name


class Response(DictNamespace, ABC):
    def __init__(self, response):
        super().__init__(response)
        jsonschema.validate(response, self._schema)

    @property
    @abstractmethod
    def _schema(self):
        pass


class ResponseList(UserList, ABC):
    def __init__(self, responses=[]):
        super().__init__(map(self._response_class, responses))

    @property
    @abstractmethod
    def _response_class(self):
        pass


def _lookup_response(*args, responses):
    if not args:
        return None

    v = responses.get(args[0])
    if isinstance(v, dict):
        return _lookup_response(*args[1:], responses=v)
    return v

def lookup_response(*args):
    v = _lookup_response(*args, responses=RESPONSES)
    if v:
        return v
    raise RuntimeError(f'No Response type found for cmd: {args}')

def R(schema):
    class InnerResponse(Response):
        @property
        def _schema(self):
            return schema
    return InnerResponse

def RL(schema):
    class InnerResponseList(ResponseList):
        @property
        def _response_class(self):
            return R(schema)
    return InnerResponseList


AccountInfo = OBJ(
    id=STR,
    name=STR,
    user=OBJ(
        name=STR,
    ),
)

ConfigVar = OBJ(
    name=STR,
    source=STR,
    value=STR,
)

LocationInfo = OBJ(
    id=STR,
    name=STR,
    displayName=STR,
    regionalDisplayName=STR,
    type=STR,
)

GroupInfo = OBJ(
    id=STR,
    name=STR,
    location=STR,
    tags=ANY(
        OBJ(),
        NULL,
    ),
)

ImageGalleryInfo = OBJ(
    id=STR,
    name=STR,
    location=STR,
    resourceGroup=STR,
    provisioningState=STR,
    type=STR,
)

ImageDefinitionInfo = OBJ(
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

StorageAccountInfo = OBJ(
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

StorageKeyInfo = OBJ(
    keyName=STR,
    value=STR,
    permissions=STR,
    creationTime=STR,
)

StorageContainerInfo = OBJ(
    name=STR,
)

StorageBlobInfo = OBJ(
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

SshKeyInfo = OBJ(
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

VMInfo = OBJ(
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

VMInstanceInfo = OBJ(
    id=STR,
    instanceView=OBJ(
        computerName=STR,
        hyperVGeneration=STR,
        osName=STR,
        osVersion=STR,
        statuses=ARRY(
            OBJ(
                code=STR,
                displayStatus=STR,
            ),
        ),
        vmAgent=OBJ(
            statuses=ARRY(
                OBJ(
                    code=STR,
                    displayStatus=STR,
                ),
            ),
            vmAgentVersion=STR,
        ),
    ),
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
        imageReference=OBJ(
            exactVersion=STR,
            offer=STR,
            publisher=STR,
            sku=STR,
            version=STR,
        ),
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

RESPONSES = {
    'account': {
        'show': R(AccountInfo),
        'list': RL(AccountInfo),
        'list-locations': RL(LocationInfo),
    },
    'config': {
        'get': R(ConfigVar),
    },
    'group': {
        'show': R(GroupInfo),
        'list': RL(GroupInfo),
    },
    'sig': {
        'show': R(ImageGalleryInfo),
        'list': RL(ImageGalleryInfo),
        'image-definition': {
            'show': R(ImageDefinitionInfo),
            'list': RL(ImageDefinitionInfo),
        },
    },
    'storage': {
        'account': {
            'show': R(StorageAccountInfo),
            'list': RL(StorageAccountInfo),
            'keys': {
                'list': RL(StorageKeyInfo),
            },
        },
        'container': {
            'show': R(StorageContainerInfo),
            'list': RL(StorageContainerInfo),
        },
        'blob': {
            'show': R(StorageBlobInfo),
            'list': RL(StorageBlobInfo),
        },
    },
    'sshkey': {
        'show': R(SshKeyInfo),
        'list': RL(SshKeyInfo),
    },
    'vm': {
        'show': R(VMInfo),
        'list': RL(VMInfo),
        'get-instance-view': R(VMInstanceInfo),
    },
}
