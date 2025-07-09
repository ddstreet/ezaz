
from .response import RESPONSES


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
