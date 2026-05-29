import logging
from platform import system

__all__ = ["SYSTEM", "REPLACEMENTS", "is_hidden"]

SYSTEM = system()

if SYSTEM == "Windows":
    from .windows import REPLACEMENTS, is_hidden
else:
    if SYSTEM != "Linux":
        logging.warning("Can't tell if this system is supported; defaulting to Linux")
    from .linux import REPLACEMENTS, is_hidden
