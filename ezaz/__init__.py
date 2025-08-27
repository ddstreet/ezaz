
import logging
import os

from pathlib import Path

from .requiredpackage import RequiredPackage


LOGGER = logging.getLogger(__name__)
AZ_TRACE_LOGGER = logging.getLogger(f'{__name__}.AZ')
LOG_VERBOSE_MIN = logging.INFO
LOG_VERBOSE_MAX = logging.DEBUG
LOG_LEVEL_V0 = LOG_VERBOSE_MIN
LOG_LEVEL_V1 = LOG_VERBOSE_MIN - 1
LOG_LEVEL_V2 = LOG_VERBOSE_MIN - 2
LOG_LEVEL_V3 = LOG_VERBOSE_MIN - 3
LOG_LEVEL_V4 = LOG_VERBOSE_MIN - 4
LOG_LEVEL_V5 = LOG_VERBOSE_MAX
LOG_V0 = lambda *args, **kwargs: LOGGER.log(LOG_LEVEL_V0, *args, **kwargs)
LOG_V1 = lambda *args, **kwargs: LOGGER.log(LOG_LEVEL_V1, *args, **kwargs)
LOG_V2 = lambda *args, **kwargs: LOGGER.log(LOG_LEVEL_V2, *args, **kwargs)
LOG_V3 = lambda *args, **kwargs: LOGGER.log(LOG_LEVEL_V3, *args, **kwargs)
LOG_V4 = lambda *args, **kwargs: LOGGER.log(LOG_LEVEL_V4, *args, **kwargs)
LOG_V5 = lambda *args, **kwargs: LOGGER.log(LOG_LEVEL_V5, *args, **kwargs)

DEFAULT_CONFIGPATH = Path(os.environ.get('XDG_CONFIG_HOME', '~/.config')) / 'ezaz'
DEFAULT_CACHEPATH = Path(os.environ.get('XDG_CACHE_HOME', '~/.cache')) / 'ezaz'

REQUIRED_PACKAGES = [
    RequiredPackage('azure-cli', programs=['az']),
    RequiredPackage('argcomplete', modules=['argcomplete']),
    RequiredPackage('cryptography', modules=['cryptography']),
    # dateparser is quite slow to load, and we're not currently using
    # it; uncomment this if anything starts using DateTimeArgConfig
    #RequiredPackage('dateparser', modules=['dateparser']),
    RequiredPackage('jsonschema', modules=['jsonschema']),
]

DISTRO_IMAGES = {
    'azl3': 'MicrosoftCBLMariner:azure-linux-3:azure-linux-3-gen2:latest',
    'lg': '/subscriptions/035db282-f1c8-4ce7-b78f-2a7265d5398c/resourceGroups/LinuxGuardPipelines/providers/Microsoft.Compute/galleries/linuxguardgallery/images/linuxguard-base/versions/latest',
    'uv': '/subscriptions/e8163038-eb55-4108-b164-1d0563f63588/resourceGroups/ddstreetwestus2rg/providers/Microsoft.Compute/galleries/ddstreetwestus2ig/images/ddstreetwestus2id/versions/latest',
    'ubuntu2204': 'Canonical:0001-com-ubuntu-server-jammy-daily:22_04-daily-lts-gen2:latest',
    'ubuntu2404': 'Canonical:ubuntu-24_04-lts-daily:server:latest',
    'ubuntults': 'Canonical:ubuntu-24_04-lts-daily:server:latest',
    'ubuntu2504': 'Canonical:ubuntu-25_04-daily:server:latest',
    'ubuntu2510': 'Canonical:ubuntu-25_10-daily:server:latest',
}
