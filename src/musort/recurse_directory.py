from collections.abc import Generator, Iterable, Mapping, Sequence
from collections.abc import Set as AbstractSet
from pathlib import Path
from typing import NewType, TypeGuard

from .mut_chain import MutChain
from .tools import is_hidden

type SupportsContainsItem[T] = Sequence[T] | AbstractSet[T] | Mapping[str, object]

Directory = NewType("Directory", Path)
MusicFile = NewType("MusicFile", Path)


def is_directory(path: Path) -> TypeGuard[Directory]:
    return path.is_dir()


def is_music_file(path: Path, music_exts: set[str]) -> TypeGuard[MusicFile]:
    return path.is_file() and path.suffix.lower() in music_exts


def recurse_music_directory(
    root: Path,
    *,
    music_exts: Iterable[str],
    ignored_names: Iterable[str],
    ignore_symlinks: bool,
    ignore_hidden: bool,
) -> Generator[MusicFile, None, None]:
    music_exts = {ext.lower() for ext in music_exts}
    ignored_names = {name.lower() for name in ignored_names}

    paths = MutChain([root])

    for path in paths:
        if path.name.lower() in ignored_names:
            continue

        if ignore_symlinks and path.is_symlink():
            continue

        if ignore_hidden and is_hidden(path):
            continue

        if is_directory(path):
            paths.aftspread(path.iterdir())

        if is_music_file(path, music_exts):
            yield path
