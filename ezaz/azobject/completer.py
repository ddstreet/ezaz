
import argcomplete

from ..cache import Cache
from ..config import Config


class AzObjectCompleter:
    def __init__(self, azclass, info_attr=None):
        self.azclass = azclass
        self.info_attr = None

    def get_instance(self, azclass, cache=None, config=None, **opts):
        if not azclass.is_child():
            return azclass(cache=Cache(cache), config=Config(config))

        parent = self.get_instance(azclass.get_parent_class(), cache=cache, config=config, **opts)
        name = azclass.azobject_name()
        opts['name'] = name
        return parent.get_specified_child(**opts) or parent.get_default_child(name)

    def __call__(self, *, prefix, action, parser, parsed_args, **kwargs):
        try:
            parent = self.get_instance(self.azclass.get_parent_class(), **vars(parsed_args))
            return map(self.get_info_attr, self.azclass.list(parent, **vars(parsed_args)))
        except Exception as e:
            if getattr(parsed_args, 'verbose', 0) > 1:
                argcomplete.warn(f'argcomplete error: {e}')
            raise

    def get_info_attr(self, info):
        if self.info_attr:
            return getattr(info, self.info_attr)
        else:
            return self.azclass.info_id(info)
