
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


AccountShow = OBJ(name=STR,
                  id=STR,
                  user=OBJ(name=STR))

ConfigGet = OBJ(name=STR,
                source=STR,
                value=STR)

GroupShow = OBJ(name=STR,
                location=STR,
                id=STR,
                tags=ANY(OBJ(), NUL))

RESPONSES = {
    "account": {
        "show": R(AccountShow),
        "list": RL(AccountShow),
    },
    "config": {
        "get": R(ConfigGet),
    },
    "group": {
        "show": R(GroupShow),
        "list": RL(GroupShow),
    },
}
