
from .. import DISTRO_IMAGES
from ..azobject.vm import VM
from .command import ActionParserConfig
from .command import CommonActionCommand
from .resourcegroup import ResourceGroupCommand


class VMCommand(CommonActionCommand):
    @classmethod
    def parent_command_cls(cls):
        return ResourceGroupCommand

    @classmethod
    def azobject_class(cls):
        return VM

    @classmethod
    def parser_get_action_parser_configs(cls):
        return (super().parser_get_action_parser_configs() +
                [ActionParserConfig('console', description='Attach to serial console'),
                 ActionParserConfig('log', description='Show serial console log'),
                 ActionParserConfig('restart', description='Restart the VM'),
                 ActionParserConfig('start', description='Start the VM'),
                 ActionParserConfig('stop', description='Stop the VM')])

    @classmethod
    def parser_add_create_action_arguments(cls, parser):
        image_group = parser.add_mutually_exclusive_group(required=True)
        image_group.add_argument('--image',
                                 help='The image id deploy')
        image_group.add_argument('--distro',
                                 choices=DISTRO_IMAGES.keys(),
                                 help='The distro to deploy')

        parser.add_argument('--no-wait',
                            action='store_true',
                            help='Do not wait for long-running operation to finish')

    @classmethod
    def parser_add_delete_action_arguments(cls, parser):
        parser.add_argument('-y', '--yes',
                            action='store_true',
                            help='Do not prompt for confirmation')
        parser.add_argument('--no-wait',
                            action='store_true',
                            help='Do not wait for long-running operation to finish')
