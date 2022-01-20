import textwrap
from pathlib import Path
from typing import Generator, Optional, TypeVar

from tinytag import TinyTag

accepted_files = (
    ".mp3",
    ".wav",
    ".flac",
    ".aiff",
    ".aifc",
    ".aif",
    ".afc",
    ".oga",
    ".ogg",
    ".opus",
    ".wma",
    ".m4b",
    ".m4a",
    ".mp4",
)


MAIN_PARAMS = None, None, None, None, None, None, "remove_empty", "rename_folders"

Param = str


def get_params(display: str, params_tuple: tuple[None | Param, ...] = MAIN_PARAMS) -> dict[Param, bool]:
    try:
        selections = int(input(display))
    except ValueError:
        raise TypeError("Please provide an integer.")
    _len = len(params_tuple)
    # Convert into binary with a fixed length.
    selections = bin(selections)[2:].zfill(_len)[:_len]
    return {param: (selections[index] == "1") for index, param in enumerate(params_tuple) if param is not None}


def is_valid_file(path: Path) -> bool:
    """Verifies a path is a music file compatible with TinyTag"""
    return path.is_file() and path.suffix.lower() in accepted_files


def is_valid_dir(path: Path) -> bool:
    """Verifies that a path is both a directory and not a git or pycache directory"""
    return path.is_dir() and path.name != ".git" and path.name != "__pycache__"


def is_album_directory(dir: Path) -> bool:
    """Verifies that a directory contains music"""
    if not dir.is_dir():
        raise ValueError(f"Argument {dir} is not a directory")
    return any(item.suffix.lower() in accepted_files for item in dir.iterdir())


replacements: tuple[tuple[str, str], ...] = (
    (": ", " - "),
    (":", ";"),
    ('"', "'"),
    ("\\", ""),
    ("/", ""),
    ("|", ""),
    ("*", "-"),
)


def fix_new_path(name: str) -> str:
    """Shortens a string & ensures it will not break as a Windows path name"""
    resp = textwrap.fill(name.strip().split(";")[0].split("\\")[0], width=50, placeholder="(...)", max_lines=1)
    for r1, r2 in replacements:
        resp = resp.replace(r1, r2)
    return resp


def fix_new_paths(*names: str) -> Generator[str, None, None]:
    """Alias for calling fix_new_path on multiple items. Returns the same length of items."""
    return (fix_new_path(name) for name in names)


def is_int(i: str | None) -> bool:
    """I don't even know anymore. I don't like files. They're bad."""
    if not i:
        return False
    try:
        int(i)
        return True
    except (ValueError, TypeError):
        return False


class AlbumStats:
    """Contains useful information about an album directory"""

    year: Optional[str]
    genre: Optional[str]
    artist: Optional[str]
    album: Optional[str]
    keys = ("year", "genre", "album", "artist")

    def __init__(self, dir: Path) -> None:
        self.year = None
        self.genre = None
        self.artist = None
        self.album = None

        self.paths = [path for path in dir.iterdir() if is_valid_file(path)]

        for tracks_checked, path in enumerate(self.paths):
            track = TinyTag.get(path)

            for key in self.keys:
                if getattr(self, key, None) is None:
                    value = getattr(track, key)
                    if key == "artist":
                        value = getattr(track, "albumartist") or value
                    elif key == "year" and is_int(value):
                        value = value[:4]
                    if value is not None:
                        setattr(self, key, str(value or "").replace("/", "-") or None)

            if (self.year and self.genre and self.album and self.artist) or (tracks_checked >= 10):
                break


def sort_root_dir(dir: Path, root_dir: Path = None, *, remove_empty: bool, **kwargs) -> None:
    r"""Sorts Albums in some directory to the root directory

    Format: <genre>/<artist>/<year>. <album>

    For example:
        * `./Symphonies Of Doom [1985]` → `./Power Metal/Blind Guardian/1985. Symphonies Of Doom`
    """
    if root_dir is None:
        root_dir = dir.resolve()

    _sort_dir(dir, root_dir, **kwargs)

    if remove_empty:
        cleanup(root_dir)


def _sort_dir(dir: Path, root_dir: Path, *, errs: list[tuple[str, str]] = None, rename_folders: bool) -> None:
    """Function called by sort_root_dir. Probably shouldn't be called directly."""
    # Recursively iterate through subdirectories
    for path in dir.iterdir():
        if is_valid_dir(path):
            _sort_dir(path, root_dir, errs=errs, rename_folders=rename_folders)

    # Actual sorting
    if rename_folders and is_album_directory(dir):
        rename(dir, root_dir, errs)


def rename(dir: Path, root_dir: Path, errs: list[tuple[str, str]] | None, *, known_genres: dict[str, str] = {}) -> None:
    """Renames an Album directory"""
    stats = AlbumStats(dir)

    # Define the name of the new directory
    genre = stats.genre if (stats.genre and stats.genre != "Other") else "UNKNOWN_GENRE"
    artist = stats.artist or "UNKNOWN_ARTIST"
    album = stats.album or "Singles"
    if stats.year is not None:
        album = stats.year + ". " + album

    genre, artist, album = fix_new_paths(genre, artist, album)
    if artist in known_genres:
        genre = known_genres[artist]
    else:
        known_genres[artist] = genre
    print(genre, artist, album)

    # Create the new directory's parent
    target_dir = root_dir / genre / artist
    target_dir.mkdir(parents=True, exist_ok=True)

    # Move into the new directory
    try:
        dir.rename(target_dir / album)
    except FileExistsError as err:
        print(err)
        if errs is not None:
            errs.append((artist, album))
    except PermissionError as err:
        if err.winerror != 5 or errs is None:
            raise err
        print(f"Access is denied for album '{artist} - {album}'.")
        errs.append((artist, album))


def cleanup(dir: Path) -> None:
    """Recursively deletes all empty directories.

    This assumes that, like on Windows, non-empty directories cannot be deleted.
    """
    for path in dir.iterdir():
        if is_valid_dir(path):
            cleanup(path)

    try:
        dir.rmdir()
    except:
        pass


# TODO: Split into smaller functions. Also, *definitely* split rename into smaller functions.
def main() -> None:
    """Asks for input before running the sort and cleanup functions.

    If no path is given, assumes current path. If path given starts with './', set root directory to current path
    and format from given path.
    """
    dirs = [str(path) for path in Path(".").iterdir() if is_valid_dir(path)]
    print(f"Subdirectories here: {', '.join(dirs)}")

    path = input("Path? ")
    root = Path(".").resolve() if path.startswith("./") else None
    path = Path(path)

    if not is_valid_dir(path):
        raise ValueError(f"Path {path.resolve()} is not a valid directory!")

    kwargs = get_params("Mode? ", MAIN_PARAMS)
    print(kwargs)
    errors: list[tuple[str, str]] = []
    sort_root_dir(path, root, errs=errors, **kwargs)
    if errors:
        print("\n\n\nErrors occurred for the following albums:")
        for error in errors:
            print(*error)


if __name__ == "__main__":
    # It is awfully convenient to catch errors.
    try:
        main()
    except Exception as e:
        print(e.__class__.__name__ + ":", e)
