import re
import textwrap
from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass
from functools import cached_property, partial
from pathlib import Path
from typing import ClassVar, NewType, cast, overload

from tinytag import TinyTag

from musort.tools import clargs
from musort.typeshed import EMPTY_MAP, SupportsItems

__all__ = ["Track"]


Genre = NewType("Genre", str)
Artist = NewType("Artist", str)
Album = NewType("Album", str)
Year = NewType("Year", int)


@dataclass
class Track:
    """Contains track file information."""

    path: Path
    """Track path."""
    tags: TinyTag
    """Extracted track metadata."""

    _GENRE_CACHE: ClassVar[dict[str, Genre | None]] = {}

    @cached_property
    def genre(self) -> Genre | None:
        genre = cast(Genre | None, self.tags.genre)
        if clargs.single_genre and (artist := self.artist):
            artist = artist.lower()
            genre = self._GENRE_CACHE.setdefault(artist, genre)
        return genre

    @cached_property
    def artist(self) -> Artist | None:
        value = self.tags.albumartist or self.tags.artist
        if value is not None:
            return cast(Artist, value.strip())

    @cached_property
    def album(self) -> Album | None:
        return self.tags.album  # pyright: ignore[reportReturnType]

    @cached_property
    def date(self) -> str | None:
        return self.tags.year

    @property
    def year(self) -> Year | None:
        date = self.date
        if not date:
            return
        year_match = re.search(r"\b\d{4}\b", date)
        if year_match is not None:
            year = year_match.group(0).lstrip("0")
            if not year:
                return 0  # pyright: ignore[reportReturnType]
            else:
                return int(year_match.group(0))  # pyright: ignore[reportReturnType]

    @property
    def year_string(self) -> str | None:
        year = self.year
        if year is not None:
            return str(self.year).zfill(4)

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

    @overload
    @staticmethod
    def prepare_component(
        comp: str, /, default: object = None, splitters: Iterable[str] = ";"
    ) -> str: ...

    @overload
    @staticmethod
    def prepare_component[T](
        comp: str | None, /, default: T = None, splitters: Iterable[str] = ";"
    ) -> T | str: ...

    @staticmethod
    def prepare_component[T](
        comp: str | None,
        default: T = None,
        splitters: Iterable[str] = ";",
        replacements: SupportsItems[str, str] | None = None,
    ) -> T | str:
        """Prepare a string for being used as a file path."""
        if comp is None:
            return default
        if replacements is None:
            replacements = EMPTY_MAP
        # handle genres split by semicolons, full dates, etc
        for splitter in splitters:
            comp = comp.split(splitter)[0].strip()
        # remove characters that result in invalid filenames
        for s0, s1 in replacements.items():
            comp = comp.replace(s0, s1)
        return comp

    truncate_component: ClassVar[Callable[[str], str]] = staticmethod(
        partial(textwrap.fill, width=80, placeholder="(…)", max_lines=1)
    )

    def get_new_dir(self) -> Iterator[str]:
        components = [
            self.prepare_component(self.genre, default="UNKNOWN GENRE"),
            self.prepare_component(self.artist, default="UNKNOWN ARTIST"),
        ]

        album = self.prepare_component(self.album, default="UNKNOWN ALBUM")
        year = self.year_string
        if year:
            album = f"{year} - {album}"
        components.append(album)

        return map(self.truncate_component, components)

    def get_new_name(self) -> str:
        track = (str(self.track) if self.track else "").zfill(2)
        title = self.prepare_component(self.title, default="UNKNOWN TRACK")
        body = self.truncate_component(f"{track} - {title}")
        suffix = self.path.suffix.lower()
        return body + suffix

    def has_complete_metadata(self) -> bool:
        return all((self.year is not None, self.genre, self.artist, self.album))
