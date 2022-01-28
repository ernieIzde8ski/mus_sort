"""
Copyright © 2022 Ernest Izdebski

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

"""
Terms as used:
    Path: A filepath.
        Music file: A filepath compatible with TinyTag.
        Directory: A directory.
            Folder: A directory which contains music files.
    Request: A function that takes an input from the command line.
    Mode: A dictionary of sorting actions.
        Modum: A single Mode.
        Modes: All available Modums.
    Options: Selected directories & mode.
"""

import textwrap
from pathlib import Path
from typing import Generator, Optional

from tinytag import TinyTag, TinyTagException


### Consts
INVALID_DIRS = ".git", "__pycache__", "downloading"
MODES = "remove_duplicates", "rename_files", "remove_empty", "rename_dirs"

MUSFILE_SUFFIXES = (
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

DEFAULT_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    (": ", " - "),
    (":", ";"),
    ('"', "'"),
    ("\\", ""),
    ("/", ""),
    ("|", ""),
    ("*", "-"),
    ("?", "❓"),
    ("...", "…"),
    (".", ""),
    ("<", "{"),
    (">", "}"),
)


Errors = list[tuple[str | None, ...]]
Modum = str
Mode = dict[Modum, bool]


### Utils
def is_music(path: Path) -> bool:
    """Verifies a path is a music file compatible with TinyTag"""
    return path.is_file() and path.suffix.lower() in MUSFILE_SUFFIXES


def is_valid_dir(path: Path) -> bool:
    """Verifies that a path is both a directory and not a git or pycache directory"""
    # TODO: Extract invalid names into tuple.
    return path.is_dir() and path.name != ".git" and path.name != "__pycache__"


def is_music_folder(dir: Path) -> bool:
    """Verifies that a directory contains music."""
    return any(item.suffix.lower() in MUSFILE_SUFFIXES for item in dir.iterdir())


def is_int(i: str | None) -> bool:
    """I don't even know anymore. I don't like files. They're bad."""
    if not i:
        return False
    try:
        int(i)
        return True
    except (ValueError, TypeError):
        return False


def fix_path(name: str, *, width: int = 50) -> str:
    """Truncates a string & ensures it will not break as a path under Windows."""
    resp = name.strip().split(";")[0].split("\\")[0]
    for r1, r2 in DEFAULT_REPLACEMENTS:
        resp = resp.replace(r1, r2)
    resp = textwrap.fill(resp, width=width, placeholder="(…)", max_lines=1)
    return resp


def fix_paths(*names: str) -> Generator[str, None, None]:
    """Alias for calling fix_path on multiple items. Returns the same length of items."""
    return (fix_path(name) for name in names)


# Sorting
class MusicFolder:
    """Contains only relevant information about a music folder"""

    year: Optional[str]
    genre: Optional[str]
    artist: Optional[str]
    album: Optional[str]
    keys = ("year", "genre", "album", "artist")

    def __init__(self, dir: Path, maxToCheck: int = 5) -> None:
        self.year = None
        self.genre = None
        self.artist = None
        self.album = None

        self.dir = dir
        self.reset = False
        paths = (path for path in dir.iterdir() if is_music(path))
        self.tracks: list[tuple[Path, TinyTag] | Generator[Path, None, None]] = []

        for i, path in enumerate(paths):
            track = TinyTag.get(path)
            self.tracks.append((path, track))

            for key in self.keys:
                if getattr(self, key, None) is None:
                    value = getattr(track, key)
                    if key == "artist":
                        value = getattr(track, "albumartist") or value
                    elif key == "year" and is_int(value):
                        value = value[:4]
                    if value is not None:
                        setattr(self, key, str(value or "").replace("/", "-") or None)

            if (self.year and self.genre and self.album and self.artist) or (i >= maxToCheck):
                break

        self.tracks.append(paths)

    def reorganize(self, errs: Errors, remove_duplicates: bool) -> None:
        if self.reset:
            self.tracks = list(((path for path in self.dir.iterdir() if is_music(path)),))
        self.reorganize_jpegs()
        self.reorganize_files(errs, remove_duplicates=remove_duplicates)

    def reorganize_jpegs(self) -> None:
        cover = self.dir / "Cover.jpg"
        folder = self.dir / "Folder.jpg"
        cover = cover, cover.exists()
        folder = folder, folder.exists()
        if cover[1]:
            if folder[1]:
                print(f"DELETE {cover[0].as_posix()}")
                cover[0].unlink(missing_ok=True)
            else:
                print(f"RENAME {cover[0].as_posix()} -> {folder[0].as_posix()}")
                cover[0].rename(folder[0])

    def reorganize_files(self, errs: Errors, remove_duplicates=False) -> None:
        for path, track in self:
            try:
                self.rename_file(path, track, rm_on_exists=remove_duplicates)
            except NotADirectoryError as err:
                print(err)
                exit()
            except Exception as err:
                print(err)
                errs.append((err.__class__.__name__, str(path.exists()) , path.as_posix()))

    def __iter__(self) -> Generator[tuple[Path, TinyTag], None, None]:
        if self.reset:
            self.tracks = list(((path for path in self.dir.iterdir() if is_music(path)),))
            self.reset = False
        for maybe_track in self.tracks:
            if isinstance(maybe_track, tuple):
                yield maybe_track
            else:
                for path in maybe_track:
                    yield path, TinyTag.get(path)

    @staticmethod
    def rename_file(p: Path, t: TinyTag, *, rm_on_exists: bool) -> None:
        p = p.resolve()
        target = f"{(t.track or '').zfill(2)} - {t.title}"
        target = p / ".." / (fix_path(target) + p.suffix)
        try:
            if p.name != target.name:
                print(f"{p.resolve().as_posix()} -> {target.name}")
                p.rename(target)
        except NotADirectoryError:
            # Linux compatibility
            target = target.resolve()
            p.rename(target)
        except FileExistsError as err:
            if rm_on_exists:
                print(f"DELETE {p.as_posix()}")
                return p.unlink()
            raise err


def sort_root(dir: Path, root: Path = None, *, errs: Errors, remove_empty: bool, **kwargs: bool) -> None:
    r"""Sorts Albums in some directory to the root directory

    Format: <genre>/<artist>/[<year> - ]<album>

    For example:
        * `./Symphonies Of Doom [1985]` → `./Power Metal/Blind Guardian/1985 - Symphonies Of Doom`
    """
    if root is None:
        root = dir.resolve()

    if kwargs["rename_files"] or kwargs["rename_dirs"]:
        _sort_dir(dir, root, errs=errs, **kwargs)

    if remove_empty:
        cleanup(root)


def _sort_dir(
    dir: Path, root: Path, *, errs: Errors, rename_dirs: bool, rename_files: bool, remove_duplicates: bool
) -> None:
    """Function called by sort_root. Probably shouldn't be called directly elsewhere."""
    # Recursively iterate through subdirectories]
    for path in dir.iterdir():
        if is_valid_dir(path):
            _sort_dir(
                path,
                root,
                errs=errs,
                rename_dirs=rename_dirs,
                rename_files=rename_files,
                remove_duplicates=remove_duplicates,
            )

    # Actual sorting
    if is_music_folder(dir):
        try:
            folder = MusicFolder(dir)
        except TinyTagException as err:
            print(err)
            if errs:
                errs.append((err.__class__.__name__, dir.as_posix()))
            return

        if rename_dirs:
            rename(folder, root, errs, remove_duplicates)
        if rename_files:
            folder.reorganize(errs, remove_duplicates)


def get_target_dir(root: Path, folder: MusicFolder, *, known_genres: dict[str, str] = {}) -> Path:
    """Returns a new target directory and adjusts the properties of folder simultaneously"""
    folder.genre = folder.genre if (folder.genre and folder.genre != "Other") else "UNKNOWN_GENRE"
    folder.artist = folder.artist or "UNKNOWN_ARTIST"
    folder.album = folder.album or "Singles"
    if folder.year is not None:
        folder.album = f"{folder.year} - {folder.album}"

    folder.genre, folder.artist, folder.album = fix_paths(folder.genre, folder.artist, folder.album)
    if folder.artist in known_genres:
        folder.genre = known_genres[folder.artist]
    else:
        known_genres[folder.artist] = folder.genre

    return root / folder.genre / folder.artist


def rename(folder: MusicFolder, root_dir: Path, errs: Errors, remove_duplicates: bool) -> None:
    """Renames a music folder"""
    # Define new directory
    target = get_target_dir(root_dir, folder)
    target.mkdir(parents=True, exist_ok=True)

    # Move into the new directory
    try:
        # TODO: "Stringly typed" so that I don't have to deal with str() and also can ignore type checker errors.
        folder.dir = folder.dir.rename(target / str(folder.album))
        folder.reset = True
        print(*((i or "").ljust(20) for i in (folder.genre, folder.artist, folder.album)))
    except FileExistsError as err:
        if errs and not remove_duplicates:
            print(err)
            errs.append((err.__class__.__name__, folder.artist, folder.album))
        if remove_duplicates:
            for i in folder.dir.iterdir():
                i.unlink()
            folder.dir.rmdir()
    except PermissionError as err:
        if err.winerror != 5 or errs is None:
            raise err
        print(f"Access is denied for album '{folder.artist} - {folder.album}'.")
        errs.append((err.__class__.__name__, folder.artist, folder.album))


def cleanup(root: Path) -> None:
    """Recursively deletes all empty directories.

    This assumes that, like on Windows, non-empty directories cannot be deleted.
    """
    for path in root.iterdir():
        if is_valid_dir(path):
            cleanup(path)

    try:
        root.rmdir()
    except:
        pass


### Interface
def request_mode(display: str = "Mode? ", modes: tuple[None | Modum, ...] = MODES, *, default: str = "") -> Mode:
    try:
        selections = int(input(display) or default)
    except ValueError:
        raise TypeError("Please provide an integer.")
    if selections == -1:
        return {modum: True for modum in modes if modum is not None}
    ln = len(modes)
    # Convert into binary with a fixed length.
    selections = bin(selections)[2:].zfill(ln)[:ln]
    return {modum: (selections[index] == "1") for index, modum in enumerate(modes) if modum is not None}


def request_dirs(display: str, default: str = "Path? ") -> tuple[Path | None, Path]:
    path = input(display) or default

    root = Path(".").resolve() if path.startswith("./") else None
    path = Path(path)
    if not is_valid_dir(path):
        raise ValueError(f"Path '{path.resolve()}' is not a valid directory!")

    return root, path


def request_opts(modes: tuple[str | None, ...]) -> tuple[Mode, Path | None, Path]:
    dirs = [str(path) for path in Path(".").iterdir() if is_valid_dir(path)]
    print(f"Subdirectories here: {', '.join(dirs)}")
    print(f"Modes: {', '.join(i or 'None' for i in modes)}")

    print()
    default_path, default_mode = ".", "3"
    print(f"Default path: '{default_path}'")
    print(f"Default mode: '{default_mode}'")

    print()
    dirs = request_dirs("Path?  ", default=default_path)
    mode = request_mode("Mode?  ", modes, default=default_mode)

    print()
    print(f"{mode=}")
    return mode, *dirs


def main() -> None:
    """Asks for input before running the sort and cleanup functions.

    If no path is given, assumes current path. If path given starts with './', set root directory to current path
    and format from given path.
    """
    kwargs, root, path = request_opts(MODES)
    errors: Errors = []
    sort_root(path, root, errs=errors, **kwargs)
    if errors:
        print("\n\n\nErrors occurred for the following paths:")
        for error in errors:
            print(*(err.ljust(15) for err in filter(None, error)))


if __name__ == "__main__":
    main()
