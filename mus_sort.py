import textwrap
from pathlib import Path
from typing import Generator, Optional

from tinytag import TinyTag

accepted_files = tuple(("." + i) for i in ("mp3", "bit", "wav", "wave", "opus",
                                           "flac", "asf", "wma", "mp4", "m4a", "m4b", "aiff", "aif", "aifc"))


def is_valid_dir(path: Path) -> bool:
    """Checks that a path is both a directory and is not a git directory"""
    return path.is_dir() and path.name != ".git" and path.name != "__pycache__"


def is_album_directory(dir: Path) -> bool:
    for item in dir.iterdir():
        if item.suffix.lower() in accepted_files:
            return True
    return False


replacements = [(": ", " - "), ]


def fix_new_path(name: str) -> str:
    """Makes a path suitable for Windows"""
    return textwrap.fill(name.strip(), width=50, placeholder="(...)", max_lines=1).replace(": ", " - ").replace(":", ";").replace("\"", "'").replace("\\", "").replace("/", "").replace("|", "")


def fix_new_paths(*names: str) -> Generator[str, None, None]:
    """Shortened method to call fix_new_path on multiple items
    Returns the same length of items"""
    return (fix_new_path(name) for name in names)


class AlbumDirStats:
    year: Optional[str]
    genre: Optional[str]
    artist: Optional[str]
    album: Optional[str]

    def __init__(self, dir: Path) -> None:
        self.dir = Path(dir)
        self.year = None
        self.genre = None
        self.artist = None
        self.album = None


def get_album_stats(dir: Path) -> AlbumDirStats:
    resp = AlbumDirStats(dir)
    filepaths = [i for i in dir.iterdir() if (i.is_file() and i.suffix.lower() in accepted_files)]

    for path in filepaths:
        track = TinyTag.get(path)

        for attr in ("year", "genre", "album", "artist"):
            if getattr(resp, attr, None) is None:
                if (_attr := getattr(track, attr)) is not None:
                    setattr(resp, attr, str(_attr).replace("/", "-") or None)

        if resp.year and resp.genre and resp.album and resp.artist:
            return resp

    return resp


def sort(dir: Path, root_dir: Path = None, *, errs: list[tuple[str, str]] = None) -> None:
    if root_dir is None:
        root_dir = dir.resolve()

    for path in dir.iterdir():
        if is_valid_dir(path):
            sort(path, root_dir, errs=errs)

    if is_album_directory(dir):
        if dir.name == ".git":
            return
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
        target_dir.resolve()

        target_dir = target_dir / album

        try:
            dir.rename(target_dir)
        except FileExistsError as err:
            print(err)
            if errs is not None:
                errs.append((artist, album))
        except PermissionError as err:
            if err.winerror == 5 and errs is not None:
                print(f"Access is denied for album '{artist} - {album}'. You listening to that?")
                errs.append((artist, album))
            else:
                raise err


def cleanup(dir: Path) -> None:
    for path in dir.iterdir():
        if is_valid_dir(path) is False:
            continue
        cleanup(path)
    try:
        dir.rmdir()
    except:
        pass


def main() -> None:
    path = Path(input("Path?  "))
    if not is_valid_dir(path):
        raise ValueError(f"Path {path.resolve()} is not a valid path" )

    errors: list[tuple[str, str]] = []
    sort(path, errs=errors)
    cleanup(Path(path))
    if len(errors) > 0:
        print("\n\n\nErrors occurred for the following albums:")
        for error in errors:
            print(*error)


if __name__ == "__main__":
    dirs = [str(path) for path in Path(".").iterdir() if is_valid_dir(path)]
    print(f"Subdirectories here: {', '.join(dirs)}")
    try:
        main()
    except Exception as e:
        print(e.__class__.__name__ + ":", e)
