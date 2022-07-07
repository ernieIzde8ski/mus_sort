import logging
from pathlib import Path
from typing import Callable
from .tools import clargs, cleanup, errors

if clargs.folder_mode:
    from .sort_folders import sort
elif clargs.file_mode:
    from .sort_files import sort
else:
    raise RuntimeError("This shouldn't happen")
sort()
logging.info("Done sorting!")

if clargs.clean_after:
    cleanup(clargs.dir)
    logging.info("Done cleaning!")


if errors:
    errors.recap()
