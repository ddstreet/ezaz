
from ..azobject.storageblob import StorageBlob
from .command import AzSubObjectActionCommand
from .storagecontainer import StorageContainerCommand


class StorageBlobCommand(AzSubObjectActionCommand):
    @classmethod
    def parent_command_cls(cls):
        return StorageContainerCommand

    @classmethod
    def azclass(cls):
        return StorageBlob

    @classmethod
    def parser_add_create_action_arguments(cls, parser):
        parser.add_argument('-f', '--file',
                            required=True,
                            help='File to upload')
        parser.add_argument('--type',
                            choices=['append', 'block', 'page'],
                            help='File to upload')
        parser.add_argument('--no-progress',
                            action='store_true',
                            help='Do not show upload progress bar')
        parser.add_argument('--overwrite',
                            action='store_true',
                            help='Overwrite an existing blob')

    @classmethod
    def parser_add_download_action_arguments(cls, parser):
        parser.add_argument('--file',
                            required=True,
                            help='File to write out to')
        parser.add_argument('--no-progress',
                            action='store_true',
                            help='Do not show upload progress bar')
