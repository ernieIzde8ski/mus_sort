import textwrap
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import ClassVar

from tinytag import TinyTag

from musort.tools import REPLACEMENTS, cache, clargs

__all__ = ["MusicFile"]


@dataclass
class MusicFile:
    """Contains music file information."""

    path: Path
    """Path to the file."""

    tags: TinyTag
    """Where data is pulled from."""

    @cached_property
    def genre(self) -> str | None:
        artist = self.artist
        if clargs.single_genre and artist:
            return cache.genre(artist, default=self.tags.genre)
        return self.tags.genre

    @cached_property
    def artist(self) -> str | None:
        return self.tags.albumartist or self.tags.artist

    @cached_property
    def album(self) -> str | None:
        return self.tags.album

    @cached_property
    def year(self) -> str | None:
        return self.tags.year

    @cached_property
    def title(self) -> str | None:
        """Name of the track."""
        return self.tags.year

    @cached_property
    def track(self) -> int | None:
        """Track number."""
        return self.tags.track

    @classmethod
    def get(cls, path: Path, /):
        """Constructs an instance of MusicFile from a path to a music file."""
        return cls(path, TinyTag.get(path))

    _FILE_SUFFIXES: ClassVar[set[str]] = {
        ".mp1",
        ".mp2",
        ".mp3",
        ".oga",
        ".ogg",
        ".opus",
        ".wav",
        ".flac",
        ".wma",
        ".m4b",
        ".m4a",
        ".m4r",
        ".aiff",
        ".aifc",
        ".aif",
        ".afc",
    }
    """Accepted file suffixes, as per `TinyTag._get_parser_for_filename`."""

    @classmethod
    def is_music(cls, path: Path):
        return path.is_file() and path.suffix.lower() in cls._FILE_SUFFIXES

    @staticmethod
    def prepare_component[T](
        tag: str | None, default: T = None, max_size: int = 70
    ) -> str | T:
        """Prepare a TinyTag component for being used as a file path."""
        if not tag:
            return default
        # sometimes a genre tag is actually multiple genres split by semicolons
        resp = tag.split(";")[0].strip()
        # remove characters that result in invalid filenames
        for s0, s1 in REPLACEMENTS.items():
            resp = resp.replace(s0, s1)
        # reducing the length of the string
        # the default being 70 is absolutely arbitrary
        return textwrap.fill(resp, width=max_size, placeholder="(…)", max_lines=1)

    def get_new_dir(self, target: Path = clargs.target, /) -> Path:
        genre = self.prepare_component(self.genre, default="UNKNOWN_GENRE")
        artist = self.prepare_component(self.artist, default="UNKNOWN_ARTIST")
        album = self.prepare_component(self.album, default="UNKNOWN_ALBUM")
        if self.year:
            album = f"{self.prepare_component(self.year)} - {album}"
        return target / genre / artist / album

    def get_new_name(self) -> str:
        track = (str(self.track) if self.track else "").zfill(2)
        title = self.prepare_component(self.title, default="UNKNOWN_TRACK")
        suffix = self.path.suffix.lower()
        return f"{track} - {title}{suffix}"

    def get_new_path(self, target: Path = clargs.target) -> Path:
        """Shorthand for `MusicFile.get_new_dir(target) / MusicFile.get_new_name()`"""
        return self.get_new_dir(target) / self.get_new_name()
