
from collections.abc import Iterable
from types import SimpleNamespace


def convert_item(item):
    if isinstance(item, list):
        return [convert_item(i) for i in item]
    if isinstance(item, dict):
        return DictNamespace(item)
    return item


# Similar to SimpleNamespace, but also converts deeply, and its attributes are iterable
class DictNamespace(SimpleNamespace, Iterable):
    def __init__(self, obj):
        assert isinstance(obj, dict), f'Unexpected obj type {type(obj)}'

        super().__init__({k: convert_item(v) for k, v in obj.items()})

    def __iter__(self):
        return iter(self.__dict__)
