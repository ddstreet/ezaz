
import jsonschema

from ..dictnamespace import DictNamespace
from ..schema import *


def R(schema):
    class _R(DictNamespace):
        def __init__(self, response):
            super().__init__(response)
            jsonschema.validate(response, schema)
    return _R

def RL(schema):
    cls = R(schema)
    class _RL(list):
        def __init__(self, responses):
            super().__init__([cls(r) for r in responses])
    return _RL


AccountInfo = OBJ(id=STR,
                  name=STR,
                  user=OBJ(name=STR))

ConfigVar = OBJ(name=STR,
                source=STR,
                value=STR)

GroupInfo = OBJ(id=STR,
                name=STR,
                location=STR,
                tags=ANY(OBJ(), NUL))

ImageGalleryInfo = OBJ(id=STR,
                       name=STR,
                       location=STR,
                       resourceGroup=STR,
                       provisioningState=STR,
                       type=STR)

ImageDefinitionInfo = OBJ(id=STR,
                          name=STR,
                          location=STR,
                          resourceGroup=STR,
                          identifier=OBJ(offer=STR, publisher=STR, sku=STR),
                          architecture=STR,
                          hyperVGeneration=STR,
                          osState=STR,
                          osType=STR,
                          tags=ANY(OBJ(), NUL))

StorageAccountInfo = OBJ(id=STR,
                         name=STR,
                         location=STR,
                         resourceGroup=STR,
                         creationTime=STR,
                         tags=ANY(OBJ(), NUL),
                         type=STR)

StorageContainerInfo = OBJ(name=STR)

SshKeyInfo = OBJ(id=STR,
                 name=STR,
                 location=STR,
                 publicKey=STR,
                 resourceGroup=STR,
                 tags=ANY(OBJ(), NUL))

RESPONSES = {
    "account": {
        "show": R(AccountInfo),
        "list": RL(AccountInfo),
    },
    "config": {
        "get": R(ConfigVar),
    },
    "group": {
        "show": R(GroupInfo),
        "list": RL(GroupInfo),
    },
    "sig": {
        "show": R(ImageGalleryInfo),
        "list": RL(ImageGalleryInfo),
        "image-definition": {
            "show": R(ImageDefinitionInfo),
            "list": RL(ImageDefinitionInfo),
        },
    },
    "storage": {
        "account": {
            "show": R(StorageAccountInfo),
            "list": RL(StorageAccountInfo),
        },
        "container": {
            "show": R(StorageContainerInfo),
            "list": RL(StorageContainerInfo),
        },
    },
    "sshkey": {
        "show": R(SshKeyInfo),
        "list": RL(SshKeyInfo),
    },
}
