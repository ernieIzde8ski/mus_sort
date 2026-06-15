import textwrap
from collections.abc import Callable, Iterable, Iterator, Set
from dataclasses import dataclass
from functools import cached_property, partial
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, Literal, Never, Protocol, overload, override

from tinytag import TinyTag

from musort.tools import cache, clargs

if TYPE_CHECKING:
    from _typeshed import SupportsItems
else:

    class SupportsItems[A, B](Protocol): ...

    class SupportsBool(Protocol): ...


class EmptyMap(SupportsItems[Never, Never]):
    @override
    def items(self) -> Set[Never]:
        return set()

    def __bool__(self) -> Literal[False]:
        return False


EMPTY_MAP = EmptyMap()


__all__ = ["Track"]


@dataclass
class Track:
    """Contains track file information."""

    path: Path
    """Track path."""
    tags: TinyTag
    """Extracted track metadata."""

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
        replacements: "SupportsItems[str, str] | None" = None,
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
        if self.year:
            year = self.prepare_component(self.year, splitters=";.-").zfill(4)
            album = f"{year} - {album}"
        components.append(album)
        return map(self.truncate_component, components)

    def get_new_name(self) -> str:
        track = (str(self.track) if self.track else "").zfill(2)
        title = self.prepare_component(self.title, default="UNKNOWN TRACK")
        body = self.truncate_component(f"{track} - {title}")
        suffix = self.path.suffix.lower()
        return body + suffix
