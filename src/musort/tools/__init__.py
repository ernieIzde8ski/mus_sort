import contextlib
from collections.abc import Iterable
from pathlib import Path

from .clargparser import clargs
from .os_locale import REPLACEMENTS, is_hidden

__all__ = ["clargs", "REPLACEMENTS", "is_hidden", "is_ok", "iterdir", "cleanup"]


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


def cleanup(dirs: Iterable[Path]):
    """Removes empty directories"""
    for dir in dirs:
        if dir.is_dir():
            cleanup(dir.iterdir())
            with contextlib.suppress(Exception):
                dir.rmdir()
