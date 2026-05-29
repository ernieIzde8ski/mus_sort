def run():
    import logging

    from .sort import sort
    from .tools import REPLACEMENTS, clargs, cleanup, errors

    if clargs.use_dashes:
        REPLACEMENTS["/"] = "-"

    sort(*clargs.dirs)
    logging.info("Done sorting!")

    if clargs.clean_after:
        cleanup(clargs.dirs)
        logging.info("Done cleaning!")

    if errors:
        errors.recap()
