
import argcomplete


class AzObjectCompleter:
    def __init__(self, azclass):
        self.azclass = azclass

    def get_list_action_config(self):
        # The actual cmdline may have a different action; we need to override with the list action
        return self.azclass.get_action_config('list')

    def get_instance(self, azclass, parsed_args):
        if not azclass.is_child():
            return azclass(cache=Cache(), config=Config(), is_parent=True, options=parsed_args)

        parent = self.get_instance(azclass.get_parent_class(), parsed_args)
        name = azclass.azobject_name()
        return parent.get_specified_child(name, **vars(parsed_args)) or parent.get_default_child(name)

    def __call__(self, *, prefix, action, parser, parsed_args, **kwargs):
        try:
            parent = self.get_instance(self.azclass.get_parent_class(), parsed_args)
            parsed_args.actioncfg = self.get_list_action_config()
            return map(self.info_attr, self.azclass.list(parent, **vars(parsed_args)))
        except Exception as e:
            if self.verbose > 1:
                import argcomplete
                argcomplete.warn(f'argcomplete error: {e}')
            raise

    def info_attr(self, info):
        return self.azclass.info_id(info)


class AzObjectNameCompleter(AzObjectCompleter):
    def info_attr(self, info):
        return info.name


