import contextlib
from collections.abc import Iterable
from pathlib import Path

from .clargparser import clargs
from .os_locale import REPLACEMENTS, is_hidden

__all__ = ["clargs", "REPLACEMENTS", "is_hidden", "is_ok", "iterdir", "cache", "cleanup"]


def is_ok(p: Path, /):
    """Checks if a given path is processable with current clargs in mind."""
    if not clargs.hidden and is_hidden(p):
        return False
    elif not clargs.symlinks and p.is_symlink():
        return False
    elif p.name.lower() in clargs.ignored_paths:
        return False
    return True


def iterdir(dir: Path, /) -> Iterable[Path]:
    for p in dir.iterdir():
        if is_ok(p):
            yield p


class cache:
    _genre: dict[str, str | None] = {}
    """Mapping of artist name to genre. Unused if --single-genre is disabled."""

    @classmethod
    def genre(cls, artist: str, default: str | None):
        """Retrieve an item from the cache."""
        if not clargs.single_genre:
            return default
        artist = artist.lower()
        if artist in cls._genre:
            return cls._genre[artist]
        cls._genre[artist] = default
        return default


def cleanup(dirs: Iterable[Path]):
    """Removes empty directories"""
    for dir in dirs:
        if dir.is_dir():
            cleanup(dir.iterdir())
            with contextlib.suppress(Exception):
                dir.rmdir()
