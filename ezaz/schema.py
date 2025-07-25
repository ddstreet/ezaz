

def OBJ(_required_keys=None, /, **properties):
    return {
        "type": "object",
        "properties": properties,
        "required": _required_keys if _required_keys is not None else list(properties.keys()),
    }

def ARRY(items):
    return {
        "type": "array",
        "items": items,
    }

def ANY(*anyOf):
    return { "anyOf": list(anyOf), }

BOOL = { "type": "boolean" }
STR = { "type": "string" }
NUM = { "type": "number" }
NULL = { "type": "null" }
