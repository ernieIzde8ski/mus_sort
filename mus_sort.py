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

import itertools
import textwrap
from collections import defaultdict
from functools import cache
from pathlib import Path
from platform import system
from typing import Generator, Iterable, Optional

from tinytag.tinytag import TinyTag, TinyTagException

### Consts
INVALID_DIRS = ".git", "__pycache__", "downloading", "iTunes"
MODES = "remove_duplicates", "rename_files", "remove_empty", "rename_dirs"
SYSTEM = system()

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

DEFAULT_REPLACEMENTS = (
    (": ", " - "),
    (":", ";"),
    ('"', "'"),
    ("\\", ""),
    ("/", ""),
    ("|", ""),
    ("*", "-"),
    ("?", "❓"),
    ("...", "…"),
    (".", "-"),
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
    return path.is_dir() and path.name not in INVALID_DIRS


def is_music_folder(dir: Path) -> bool:
    """Verifies that a directory contains music."""
    return any(item.suffix.lower() in MUSFILE_SUFFIXES for item in dir.iterdir())


def is_int(i: str) -> bool:
    """I don't even know anymore. I don't like files. They're bad."""
    try:
        int(i)
        return True
    except (ValueError, TypeError):
        return False


def fix_path(name: str, *, width: int = 50, strict: bool = False) -> str:
    """Truncates a string & ensures it will not break as a path under Windows."""
    resp = name.strip().split(";")[0].split("\\")[0]
    if strict:
        resp = resp.split(",")[0]
    for r1, r2 in DEFAULT_REPLACEMENTS:
        resp = resp.replace(r1, r2)
    resp = textwrap.fill(resp, width=width, placeholder="(…)", max_lines=1)
    return resp


def genre(artist: str, possible: str, *, __obj: dict[str, str] = {}) -> str:
    """Abuse of mutable arguments. Do not pass any arguments for __obj. Returns a cached value if possible, else `possible`."""
    if not __obj.get(artist):
        __obj[artist] = possible
    return __obj[artist]


# Sorting
class MusicFolder:
    """Contains relevant information about a music folder"""

    year: Optional[str]
    genre: Optional[str]
    artist: Optional[str]
    album: Optional[str]
    keys = ("year", "genre", "album", "artist")

    dir: Path
    tracks: Iterable[tuple[Path, TinyTag]]

    def __init__(self, dir: Path, maxToCheck: int = 5) -> None:
        self.year = None
        self.genre = None
        self.artist = None
        self.album = None

        self.dir = dir
        paths = filter(is_music, dir.iterdir())
        known_tracks: Iterable[tuple[Path, TinyTag]] = []

        for i, path in enumerate(paths):
            track = TinyTag.get(path)
            known_tracks.append((path, track))

            for key in self.keys:
                if getattr(self, key, None) is None:
                    value: str | None = getattr(track, key)
                    if key == "artist":
                        value = getattr(track, "albumartist") or value
                    elif key == "year" and value:
                        value = value.split("-")[0]
                        if is_int(value):
                            value = value[:4]
                    if value is not None:
                        setattr(self, key, str(value or "").replace("/", "-") or None)

            if all(getattr(self, __k, None) for __k in self.keys) or (i >= maxToCheck):
                break

        paths = map(lambda p: (p, TinyTag.get(p)), paths)
        self.tracks = itertools.chain(known_tracks, paths)

    def __iter__(self) -> Generator[tuple[Path, TinyTag], None, None]:
        yield from self.tracks

    def autopath(self, root: Path, create_parents=False) -> Path:
        """Returns a new path for the folder based on the folder's attributes. May adjust said attributes."""
        self.artist = fix_path(self.artist or "UNKNOWN_ARTIST")
        self.album = fix_path(self.album or "Singles")
        self.year = fix_path(self.year or "")
        self.genre = fix_path(self.genre if (self.genre and self.genre != "Other") else "UNKNOWN_GENRE", strict=True)
        self.genre = genre(self.artist, self.genre)

        album = f"{self.year} - {self.album}" if self.year else self.album
        resp = root / self.genre / self.artist / album

        if create_parents:
            resp.parent.mkdir(exist_ok=True, parents=True)

        return resp

    def rename(self, target: str | Path) -> Path:
        self.dir = self.dir.rename(target)
        self.reset_known_paths()
        return self.dir

    def reset_known_paths(self):
        """Resets paths of music files."""
        self.tracks = ((path, TinyTag.get(path)) for path in filter(is_music, self.dir.iterdir()))

    def reorganize(self, errs: Errors, remove_duplicates: bool) -> None:
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
                errs.append((err.__class__.__name__, path.as_posix()))

    @staticmethod
    def rename_file(p: Path, t: TinyTag, *, rm_on_exists: bool) -> None:
        p = p.resolve()
        target = f"{(t.track or '').zfill(2)} - {t.title}"
        target = p / ".." / (fix_path(target) + p.suffix)
        if SYSTEM == "Linux":
            target = target.resolve()
            # This raises an error otherwise
            # I'm not complaining too much though, seeing as this script goes
            # like a million times faster under Linux than Windows.
        try:
            if p.name != target.name:
                print(f"{p.resolve().as_posix()} -> {target.name}")
                p.rename(target)
        except FileExistsError as err:
            if rm_on_exists:
                print(f"DELETE {p.as_posix()}")
                return p.unlink()
            raise err from err


def sort_root(root: Path, dir: Path, *, errs: Errors, remove_empty: bool, **kwargs: bool) -> None:
    r"""Sorts Albums in some directory to the root directory

    Format: <genre>/<artist>/[<year> - ]<album>

    For example:
        * `./Symphonies Of Doom [1985]` → `./Power Metal/Blind Guardian/1985 - Symphonies Of Doom`
    """
    if kwargs["rename_files"] or kwargs["rename_dirs"]:
        # Funny things happen when you try and rename the directory you´re currently inside
        for path in dir.iterdir():
            if is_valid_dir(path):
                sort_dir(root, path, errs=errs, **kwargs)

    if remove_empty:
        cleanup(root)
        if root != dir:
            cleanup(dir)


def sort_dir(
    root: Path, dir: Path, *, errs: Errors, rename_dirs: bool, rename_files: bool, remove_duplicates: bool
) -> None:
    """Function called by sort_root. Probably shouldn't be called directly elsewhere."""
    # Recursively iterate through subdirectories
    for path in dir.iterdir():
        if is_valid_dir(path):
            sort_dir(
                root,
                path,
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
            rename_folder(root, folder, errs, remove_duplicates)
        if rename_files:
            folder.reorganize(errs, remove_duplicates)


def rename_folder(root: Path, folder: MusicFolder, errs: Errors, remove_duplicates: bool) -> None:
    """Renames a music folder"""
    # Define new directory
    target = folder.autopath(root, create_parents=True)

    # Move into the new directory
    try:
        # TODO: "Stringly typed" so that I don't have to deal with str() and also can ignore type checker errors.
        folder.rename(target)
        print(*((i or "").ljust(25) for i in (folder.genre, folder.artist, folder.album)))

    except FileExistsError as err:
        if errs is None:
            raise err from err
        elif remove_duplicates:
            for i in folder.dir.iterdir():
                i.unlink()
            folder.dir.rmdir()
        else:
            print(err)
            errs.append((err.__class__.__name__, folder.artist, folder.album))

    except PermissionError as err:
        if getattr(err, "winerror", None) != 5 or errs is None:
            raise err from err
        print(f"Access is denied for album '{folder.artist} - {folder.album}'.")
        errs.append((err.__class__.__name__, folder.artist, folder.album))


def cleanup(root: Path) -> None:
    """Recursively deletes all empty directories.

    This assumes that, like on Windows (and Linux!), non-empty directories cannot be deleted.
    """
    for path in root.iterdir():
        if is_valid_dir(path):
            cleanup(path)


### Interface
@cache
def get_command_line_args(argv: list[str] | None = None):
    if not argv:
        from sys import argv
        argv = argv[1:]

    key = ""
    resp: dict[str, list[str]] = defaultdict(list)
    for token in argv:
        if token.startswith("-") and not is_int(token):
            key = token[1:].lower()
        else:
            resp[key].append(token)
    return resp


def _validate_value(val: str, default: str, remove_whitespace: bool) -> str:
    """Validates command-line arguments"""
    if remove_whitespace:
        val = "".join(val.split())
    if not val or val == "default":
        return default
    return val


def request_value(accepted_args: list[str], prompt: str, default: str = "", remove_whitespace=True):
    cmd_args = get_command_line_args()
    for arg in accepted_args:
        resp = " ".join(cmd_args[arg])
        if resp:
            return _validate_value(resp, default, remove_whitespace)
    return _validate_value(input(prompt), default, remove_whitespace)


def request_mode(display: str = "Mode? ", modes: tuple[None | Modum, ...] = MODES, *, default: str = "") -> Mode:
    val = request_value(["m", "-mode"], display, default)
    try:
        selections = int(val)
    except ValueError as err:
        raise TypeError(f"Value '{val}' is not a valid integer") from err
    if selections == -1:
        return {modum: True for modum in modes if modum is not None}
    ln = len(modes)
    # Convert into binary with a fixed length.
    selections = bin(selections)[2:].zfill(ln)[:ln]
    return {modum: (selections[index] == "1") for index, modum in enumerate(modes) if modum is not None}


def request_dirs(prompt: str, default: str = "") -> tuple[Path, Path]:
    val = request_value(["p", "-path"], prompt, default, remove_whitespace=False)
    path = Path(val).resolve()
    root = Path().resolve() if val.startswith("./") else path

    if not is_valid_dir(path):
        raise ValueError(f"Path '{path.resolve()}' is not a valid directory!")

    return root, path


def request_opts(modes: tuple[str | None, ...]) -> tuple[Mode, Path, Path]:
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

    print("Selected root:", dirs[0].as_posix())
    print("Selected path:", dirs[1].as_posix())
    print("Selected modes:", ", ".join(i for i in mode if mode[i]) or None)
    print()

    return mode, *dirs


def main() -> None:
    """Asks for input before running the sort and cleanup functions.

    If no path is given, assumes current path. If path given starts with './', set root directory to current path
    and format from given path.
    """
    kwargs, root, path = request_opts(MODES)
    errors: Errors = []
    sort_root(root, path, errs=errors, **kwargs)
    if errors:
        print("\n\n\nErrors occurred for the following paths:")
        for error in errors:
            print(*(err.ljust(15) for err in filter(None, error)))


if __name__ == "__main__":
    main()
