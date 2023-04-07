import errno
import logging
from pathlib import Path

from tinytag.tinytag import TinyTagException

from . import tools
from .tools import MusicFile, Suppress, clargs

common_exceptions = TinyTagException, OSError


def rename_file_in_place(path: Path) -> Path:
    music = MusicFile.get(path)
    old_name = path.as_posix()
    new_path = path.parent / music.get_new_name()

    if path == new_path:
        logging.debug(f"File at `{old_name}` is equal to new path, short-circuiting")
        return path

    try:
        path.rename(new_path)
        logging.info(f"Renamed {old_name} -> {new_path.as_posix()}")
    except FileExistsError:
        if not clargs.replace_duplicates:
            raise
        # you can accidentally delete a bunch of files if it all has no ID3 tags whatsoever,
        # so this prevents that
        if not music.track or not music.title:
            logging.debug(f"Ignoring possible duplicate at {old_name}", "ID3 tags may be missing")
            raise
        path.replace(new_path)
        logging.info(f"Replaced {old_name} -> {new_path.as_posix()}")
    return new_path


def replace_folder(source: Path, target: Path):
    for sfile in source.iterdir():
        if sfile.is_symlink():
            continue
        tfile = target / sfile.name
        if sfile.is_file():
            sfile.replace(tfile)
        elif sfile.is_dir():
            tfile.mkdir(exist_ok=True)
            replace_folder(sfile, tfile)


def sort_music_folder(music: MusicFile) -> None:
    """Sort a folder containing a music file."""
    source = music.path.parent
    target = music.get_new_dir()

    if source == target:
        logging.debug(f"Directory at `{source}` is equal to new directory, short-circuiting")
        return

    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            raise FileExistsError(str(target))
        source.rename(target)
        logging.info(f"Renamed {source.as_posix()} -> {target.as_posix()}")
    except OSError as err:
        if not clargs.replace_duplicates:
            raise

        # the error must be either a) directory not empty or b) file already exists
        if not (err.errno == errno.ENOTEMPTY or isinstance(err, FileExistsError)):
            raise

        if not music.artist or not music.album:
            logging.debug(
                f"Ignoring possible duplicate at {source.as_posix()}; ID3 tags may be missing"
            )
            raise

        replace_folder(source, target)
        logging.info(f"Replaced {source.as_posix()} -> {target.as_posix()}")


def sort_folder(dir: Path) -> None:
    """Sort a given folder and all subfolders."""

    # folders containing a .musort_ignore file are unconditionally skipped
    if (dir / ".musort_ignore").exists():
        logging.debug(f"short-circuiting, .musort_ignore file found in {dir}")
        return

    music_path: Path | None = None

    for path in tools.iterdir(dir):
        if path.is_dir():
            sort(path)
        elif (clargs.file_mode or not music_path) and MusicFile.is_music(path):
            path = path.resolve()
            if clargs.file_mode:
                with Suppress(*common_exceptions, path=path):
                    music_path = rename_file_in_place(path)
                    logging.debug(f"Assigned music_path value to {music_path.as_posix()}")
            elif not music_path:
                # upon finding a music file, we save it for later
                # I think this could probably cause some minimal lag but w/e
                music_path = path
                logging.debug(f"Found music file at {music_path.as_posix()}")

    if music_path is not None:
        with Suppress(*common_exceptions, path=music_path):
            sort_music_folder(MusicFile.get(music_path))


def sort(*dirs: Path):
    for dir in dirs:
        if not dir.is_dir():
            logging.error(f"error: path is not a directory: {dir}")
        else:
            sort_folder(dir)
