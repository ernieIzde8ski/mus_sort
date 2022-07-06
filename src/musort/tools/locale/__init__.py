import logging
from platform import system


SYSTEM = system()

if SYSTEM == "Windows":
    from .windows import *
else:
    if SYSTEM != "Linux":
        logging.warning("Can't tell if this system is supported; defaulting to Linux")
    from .linux import *
