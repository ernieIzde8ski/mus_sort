from .info import *


def run():
    import logging
    from .tools import clargs, cleanup, errors, REPLACEMENTS

    if clargs.use_dashes:
        REPLACEMENTS["/"] = "-"

    if clargs.folder_mode:
        from .sort_folders import sort
    elif clargs.file_mode:
        from .sort_files import sort
    else:
        raise RuntimeError("This shouldn't happen")

    sort(*clargs.dirs)
    logging.info("Done sorting!")

    if clargs.clean_after:
        for dir in clargs.dirs:
            cleanup(dir)
        logging.info("Done cleaning!")

    if errors:
        errors.recap()
