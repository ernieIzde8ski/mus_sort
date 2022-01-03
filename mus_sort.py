import textwrap
from pathlib import Path
from typing import Generator, Optional

from tinytag import TinyTag

accepted_files = ('.mp3', '.wav', '.flac', '.aiff', '.aifc', '.aif', '.afc', '.oga', '.ogg', '.opus', '.wma',
                  '.m4b', '.m4a', '.mp4')


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


replacements = (": ", " - "), (":", ";"), ("\"", "'"), ("\\", ""), ("/", ""), ("|", "")


def fix_new_path(name: str) -> str:
    """Shortens a string & ensures it will not break as a Windows path name"""
    resp = textwrap.fill(name.strip(), width=50, placeholder="(...)", max_lines=1)
    for r1, r2 in replacements:
        resp = resp.replace(r1, r2)
    return resp


def fix_new_paths(*names: str) -> Generator[str, None, None]:
    """Alias for calling fix_new_path on multiple items. Returns the same length of items."""
    return (fix_new_path(name) for name in names)


class AlbumStats:
    """Contains useful information about an album directory"""
    year: Optional[str]
    genre: Optional[str]
    artist: Optional[str]
    album: Optional[str]
    keys = ("year", "genre", "album", "artist")

    def __init__(self, dir: Path) -> None:
        self.dir = Path(dir)
        self.year = None
        self.genre = None
        self.artist = None
        self.album = None

        paths = [path for path in dir.iterdir() if is_valid_file(path)]
        tracks_checked = 0

        for path in paths:
            track = TinyTag.get(path)

            for key in self.keys:
                if getattr(self, key, None) is None:
                    value = getattr(track, key)
                    if key == "artist":
                        value = getattr(track, "albumartist") or value
                    if value is not None:
                        setattr(self, key, str(value or "").replace("/", "-") or None)

            tracks_checked += 1
            if (self.year and self.genre and self.album and self.artist) or (tracks_checked >= 10):
                break


def sort(dir: Path, root_dir: Path = None, *, errs: list[tuple[str, str]] = None) -> None:
    r"""Sorts Albums in a directory to the root directory

    Format: <genre>/<artist>/<year>. <album>

    For example:
        * `./Symphonies Of Doom [1985]` → `./Power Metal/Blind Guardian/1985. Symphonies Of Doom`
    """
    if root_dir is None:
        root_dir = dir.resolve()

    # Recursively iterate through subdirectories
    for path in dir.iterdir():
        if is_valid_dir(path):
            sort(path, root_dir, errs=errs)

    # Actual sorting
    if is_album_directory(dir):
        rename(dir, root_dir, errs)

def rename(dir, root_dir, errs):
    """Renames an Album directory"""
    stats = AlbumStats(dir)

    # Define the name of the new directory
    genre = stats.genre if (stats.genre and stats.genre != "Other") else "UNKNOWN_GENRE"
    artist = stats.artist or "UNKNOWN_ARTIST"
    album = stats.album or "Singles"
    if stats.year is not None:
        album = stats.year + ". " + album

    genre, artist, album = fix_new_paths(genre, artist, album)
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


def main() -> None:
    """Asks for input before running the sort and cleanup functions.

    If no path is given, assumes current path. If path given starts with './', set root directory to current path
    and format from given path.
    """
    dirs = [str(path) for path in Path(".").iterdir() if is_valid_dir(path)]
    print(f"Subdirectories here: {', '.join(dirs)}")

    path = input("Path?  ")
    root = Path(".").resolve() if path.startswith("./") else None
    path = Path(path)

    if not is_valid_dir(path):
        raise ValueError(f"Path {path.resolve()} is not a valid directory")

    errors: list[tuple[str, str]] = []
    sort(path, root, errs=errors)
    if errors:
        print("\n\n\nErrors occurred for the following albums:")
        for error in errors:
            print(*error)
    cleanup(path)


if __name__ == "__main__":
    # It is awfully convenient to catch errors.
    try:
        main()
    except Exception as e:
        print(e.__class__.__name__ + ":", e)
