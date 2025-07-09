

def OBJ(**properties):
    return {
        "type": "object",
        "properties": properties,
        "required": list(properties.keys()),
    }

def ARY(items):
    return {
        "type": "array",
        "items": items,
    }

def ANY(*anyOf):
    return { "anyOf": list(anyOf), }

STR = { "type": "string" }
NUM = { "type": "number" }
NUL = { "type": "null" }
