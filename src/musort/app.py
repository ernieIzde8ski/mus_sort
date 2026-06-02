def run():
    from loguru import logger

    from .sort import sort
    from .tools import REPLACEMENTS, clargs, cleanup

    if clargs.use_dashes:
        REPLACEMENTS["/"] = "-"

    sort(*clargs.dirs)
    logger.info("Done sorting!")

    if clargs.clean_after:
        cleanup(clargs.dirs)
        logger.info("Done cleaning!")
