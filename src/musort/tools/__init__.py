import contextlib
import logging
from collections.abc import Iterable
from pathlib import Path
from types import TracebackType
from typing import override

from .clargparser import clargs
from .os_locale import REPLACEMENTS, is_hidden

__all__ = [
    "clargs",
    "REPLACEMENTS",
    "is_hidden",
    "Errors",
    "errors",
    "Suppress",
    "is_ok",
    "iterdir",
    "cache",
    "cleanup",
]


class Errors(list[tuple[str, str | None]]):
    """Error handling. A list of tracebacks and posix-formatted paths."""

    def log(
        self,
        exc_type: type[BaseException],
        exc_val: BaseException,
        _exc_tb: TracebackType,
        path: Path | None = None,
    ):
        posix = path.as_posix() if path is not None else None
        self.append((f"{exc_type.__name__}: {exc_val}", posix))
        logging.exception(f"The following error occurred at: {posix}")

    def recap(self):
        print("\n" + ("─" * 30))
        print("\nThe following errors occurred:\n")
        for tb, p in self:
            if p:
                print(f"Path: {p}")
            print(tb)


errors = Errors()


class Suppress(contextlib.suppress):
    """Overload to contextlib.suppress to also log to `errors` object."""

    def __init__(
        self,
        *exceptions: type[BaseException],
        path: Path | None = None,
        errs_cls: Errors = errors,
    ) -> None:
        self.path = path
        self.errors = errs_cls
        super().__init__(*exceptions)

    @override
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ):

        if exc_type is not None and exc_val is not None and exc_tb is not None:
            self.errors.log(exc_type, exc_val, exc_tb, path=self.path)
        return super().__exit__(exc_type, exc_val, exc_tb)


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
