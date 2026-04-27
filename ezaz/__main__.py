
# PYTHON_ARGCOMPLETE_OK

import os
import time
os.environ['EZAZ_START_TIMESTAMP'] = str(time.perf_counter())

from .main import main


if __name__ == '__main__':
    import sys
    sys.exit(main())
