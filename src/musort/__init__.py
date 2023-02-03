from .info import *


def run():
    import logging
    from .tools import clargs, cleanup, errors, REPLACEMENTS

    if clargs.use_dashes:
        slash_index = next(i for i, v in enumerate(REPLACEMENTS) if v[0] == "/")
        REPLACEMENTS[slash_index] = ("/", "-")

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
