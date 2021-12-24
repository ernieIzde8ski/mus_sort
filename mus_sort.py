import textwrap
from pathlib import Path
from typing import Generator, Optional

from tinytag import TinyTag
accepted_files = ('.mp3', '.wav', '.flac', '.aiff', '.aifc', '.aif', '.afc', '.oga', '.ogg', '.opus', '.wma',
                  '.m4b', '.m4a', '.mp4')


def is_valid_file(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in accepted_files


def is_valid_dir(path: Path) -> bool:
    """Checks that a path is both a directory and not a git or pycache directory"""
    return path.is_dir() and path.name != ".git" and path.name != "__pycache__"


def is_album_directory(dir: Path) -> bool:
    for item in dir.iterdir():
        if item.suffix.lower() in accepted_files:
            return True
    return False


replacements = (": ", " - "), (":", ";"), ("\"", "'"), ("\\", ""), ("/", ""), ("|", "")


def fix_new_path(name: str) -> str:
    """Shortens a string & ensures it will not break as a Windows path name"""
    resp = textwrap.fill(name.strip(), width=50, placeholder="(...)", max_lines=1)
    for r1, r2 in replacements:
        resp = resp.replace(r1, r2)
    return resp


def fix_new_paths(*names: str) -> Generator[str, None, None]:
    """Shortened method to call fix_new_path on multiple items

    Returns the same length of items"""
    return (fix_new_path(name) for name in names)


class AlbumDirStats:
    year: Optional[str]
    genre: Optional[str]
    artist: Optional[str]
    album: Optional[str]

    def __init__(self, dir: Path, *,
                 year: str = None, genre: str = None, artist: str = None, album: str = None) -> None:
        self.dir = Path(dir)
        self.year = year
        self.genre = genre
        self.artist = artist
        self.album = album


def get_album_stats(dir: Path) -> AlbumDirStats:
    resp = AlbumDirStats(dir)
    paths = [path for path in dir.iterdir() if is_valid_file(path)]
    tracks_checked = 0
    for path in paths:
        track = TinyTag.get(path)

        for key in ("year", "genre", "album", "artist"):
            if getattr(resp, key, None) is None:
                value = getattr(track, key)
                if key == "artist":
                    value = getattr(track, "albumartist") or value
                if value is not None:
                    setattr(resp, key, str(value or "").replace("/", "-") or None)

        tracks_checked += 1
        if (resp.year and resp.genre and resp.album and resp.artist) or (tracks_checked >= 10):
            return resp

    return resp


def sort(dir: Path, root_dir: Path = None, *, errs: list[tuple[str, str]] = None) -> None:
    if root_dir is None:
        root_dir = dir.resolve()

    for path in dir.iterdir():
        if is_valid_dir(path):
            sort(path, root_dir, errs=errs)

    if is_album_directory(dir):
        stats = get_album_stats(dir)

        genre = stats.genre if (stats.genre and stats.genre != "Other") else "UNKNOWN_GENRE"
        artist = stats.artist or "UNKNOWN_ARTIST"
        album = stats.album or "Singles"
        if stats.year is not None:
            album = stats.year + ". " + album

        genre, artist, album = fix_new_paths(genre, artist, album)
        print(genre, artist, album)

        target_dir = root_dir / genre / artist
        target_dir.mkdir(parents=True, exist_ok=True)
        target_dir /= album

        try:
            dir.rename(target_dir)
        except FileExistsError as err:
            print(err)
            if errs is not None:
                errs.append((artist, album))
        except PermissionError as err:
            # WinError 5 always occurs when an album is being listened to through MusicBee.
            if err.winerror == 5 and errs is not None:
                print(f"Access is denied for album '{artist} - {album}'.")
                errs.append((artist, album))
            else:
                raise err


def cleanup(dir: Path) -> None:
    """Deletes all empty directories. 

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
    if len(errors) > 0:
        print("\n\n\nErrors occurred for the following albums:")
        for error in errors:
            print(*error)
    cleanup(path)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(e.__class__.__name__ + ":", e)
