from pathlib import Path

from tinytag.tinytag import TinyTagException

from . import tools
from .tools import MusicFile, clargs, logging, Suppress

common_exceptions = TinyTagException, FileExistsError, PermissionError


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


def sort_folder(music: MusicFile) -> None:
    """Sort a folder containing a music file."""
    dir = music.path.parent
    old_name = dir.as_posix()
    new_dir = music.get_new_dir()

    if dir == new_dir:
        logging.debug(f"Directory at `{dir}` is equal to new directory, short-circuiting")
        return

    try:
        new_dir.parent.mkdir(parents=True, exist_ok=True)
        dir.rename(new_dir)
        logging.info(f"Renamed {old_name} -> {new_dir.as_posix()}")
    except FileExistsError:
        if not clargs.replace_duplicates:
            raise
        # same comments as in rename_file_in_place apply
        if not music.artist or not music.album:
            logging.debug(f"Ignoring possible duplicate at {old_name}", "ID3 tags may be missing")
            raise
        dir.replace(new_dir)
        logging.info(f"Replaced {old_name} -> {new_dir.as_posix()}")


def sort(dir: Path = clargs.dir, /) -> None:
    """Sort a given folder and all subfolders."""
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
            sort_folder(MusicFile.get(music_path))
