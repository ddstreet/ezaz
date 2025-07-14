

def OBJ(**properties):
    return {
        "type": "object",
        "properties": properties,
        "required": list(properties.keys()),
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
